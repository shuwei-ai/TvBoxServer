export interface InviteCodeItem {
  id?: string
  code: string
  status: 'UNUSED' | 'USED' | 'EXPIRED' | string
  created_by?: string
  used_by?: string
  created_at?: string
  used_at?: string
}

export interface MyInvitesResponse {
  codes: InviteCodeItem[]
}

export interface GenerateInviteResponse {
  code: string
  status: string
}
