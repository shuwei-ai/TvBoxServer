import asyncio
from app.config import Settings
from app.repository import Repository


def test_device_unbind_and_default_succession():
    async def _run():
        settings = Settings(admin_openids=("admin_openid",))
        repo = Repository(config=settings, force_memory=True)
        await repo.initialize()

        # 1. 登录管理员并生成邀请码，供测试用户注册
        admin = await repo.login_or_register_by_openid("admin_openid")
        invites = await repo.create_invites(admin, 1)
        invite_code = invites[0]["code"]

        # 2. 注册普通用户
        user = await repo.login_or_register_by_openid("user_test_unbind", invite_code=invite_code)
        user_id = user["_id"]

        # 3. 绑定 3 台设备
        dev1, _ = await repo.bind_device(user_id, "tv_dev_1", "客厅电视")
        dev2, _ = await repo.bind_device(user_id, "tv_dev_2", "卧室电视")
        dev3, _ = await repo.bind_device(user_id, "tv_dev_3", "书房电视")

        # 验证初始状态：dev1 是默认设备
        assert dev1["is_default"] is True
        assert dev2["is_default"] is False
        assert dev3["is_default"] is False

        devices = await repo.list_devices(user_id)
        assert len(devices) == 3

        # 4. 通过硬件 device_id 解绑 dev2（非默认设备）
        deleted_dev2 = await repo.delete_device(user_id, "tv_dev_2")
        assert deleted_dev2 is not None
        assert deleted_dev2["device_id"] == "tv_dev_2"

        devices = await repo.list_devices(user_id)
        assert len(devices) == 2
        assert {d["device_id"] for d in devices} == {"tv_dev_1", "tv_dev_3"}

        # 验证 dev1 仍然是默认设备
        dev1_current = await repo.find_device(user_id, "tv_dev_1")
        assert dev1_current["is_default"] is True

        # 5. 通过内部 _id 解绑 dev1（当前默认设备）
        deleted_dev1 = await repo.delete_device(user_id, dev1["_id"])
        assert deleted_dev1 is not None
        assert deleted_dev1["device_id"] == "tv_dev_1"

        # 验证自动继承：dev3 应该自动成为默认设备
        devices = await repo.list_devices(user_id)
        assert len(devices) == 1
        assert devices[0]["device_id"] == "tv_dev_3"
        assert devices[0]["is_default"] is True

    asyncio.run(_run())


def test_admin_force_unbind_device():
    async def _run():
        settings = Settings(admin_openids=("admin_openid",))
        repo = Repository(config=settings, force_memory=True)
        await repo.initialize()

        # 1. 登录管理员并生成邀请码
        admin = await repo.login_or_register_by_openid("admin_openid")
        invites = await repo.create_invites(admin, 1)
        invite_code = invites[0]["code"]

        # 2. 注册普通用户并绑定设备
        user = await repo.login_or_register_by_openid("user_device_owner", invite_code=invite_code)
        dev1, _ = await repo.bind_device(user["_id"], "tv_dev_admin_test", "会议室电视")

        assert len(await repo.list_devices(user["_id"])) == 1

        # 3. 管理员强制解绑（通过 device_id）
        deleted = await repo.admin_delete_device("tv_dev_admin_test")
        assert deleted is not None
        assert deleted["device_id"] == "tv_dev_admin_test"
        assert deleted["user_id"] == user["_id"]

        # 验证已解绑
        assert len(await repo.list_devices(user["_id"])) == 0

        # 再次解绑不存在的设备返回 None
        assert await repo.admin_delete_device("tv_dev_admin_test") is None

    asyncio.run(_run())
