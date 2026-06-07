import { NextRequest, NextResponse } from 'next/server'

export async function POST(req: NextRequest) {
  const { password } = await req.json()

  const correctPassword = process.env.AUTH_PASSWORD
  const tokenValue = process.env.AUTH_TOKEN_VALUE

  if (!correctPassword || !tokenValue) {
    return NextResponse.json({ error: 'サーバー設定エラー' }, { status: 500 })
  }

  if (password !== correctPassword) {
    return NextResponse.json({ error: 'パスワードが違います' }, { status: 401 })
  }

  const res = NextResponse.json({ ok: true })
  res.cookies.set('auth_token', tokenValue, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: 60 * 60 * 24 * 30, // 30日
  })
  return res
}
