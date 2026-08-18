import asyncio
import pytest
from app.config import Settings
from app.repository import Repository, QuotaError, ConflictError
from app.dreamauth import DreamAuthClient, DreamAuthException


def test_repository_memory_wechat_login_and_register():
    async def _run():
        # 测试内存模式下的微信用户自动注册与登录
        settings = Settings(
            admin_openids=("admin_wx_openid_123",),
        )
        repo = Repository(config=settings, force_memory=True)
        await repo.initialize()

        # 1. 登录预设管理员微信用户（不需要邀请码）
        admin_user = await repo.login_or_register_by_openid("admin_wx_openid_123")
        assert admin_user["openid"] == "admin_wx_openid_123"
        assert admin_user["role"] == "ADMIN"

        # 2. 生成邀请码
        invites = await repo.create_invites(admin_user, 1)
        invite_code = invites[0]["code"]

        # 3. 注册普通微信用户（使用有效邀请码）
        user1 = await repo.login_or_register_by_openid("user_openid_001", invite_code=invite_code)
        assert user1["openid"] == "user_openid_001"
        assert user1["role"] == "USER"
        assert user1["status"] == 1
        assert user1["username"].startswith("wx_")

        # 4. 再次登录同一微信用户
        user1_again = await repo.login_or_register_by_openid("user_openid_001")
        assert user1_again["_id"] == user1["_id"]
        assert user1_again["last_login_at"] is not None

        # 5. 禁用用户后拒绝登录
        await repo.set_user_status(user1["_id"], 0)
        try:
            await repo.login_or_register_by_openid("user_openid_001")
            assert False, "Should have raised QuotaError for disabled user"
        except QuotaError as exc:
            assert "禁用" in str(exc)

    asyncio.run(_run())


def test_dreamauth_sign_logic():
    # 测试 DreamAuth 签名生成逻辑
    settings = Settings(
        dreamauth_access_key="test_ak",
        dreamauth_secret_key="test_sk_123456",
        dreamauth_app_code="APP_TEST"
    )
    client = DreamAuthClient(config=settings)
    assert client.is_configured() is True

    sign = client._sign("POST", "/api/open/scan-login/session/create", "1700000000", "nonce123", {"bizCode": "LOGIN"})
    assert isinstance(sign, str)
    assert len(sign) == 32
