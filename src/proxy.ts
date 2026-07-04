import { NextRequest, NextResponse } from 'next/server'

export function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl

  // 認証不要なパス（apple-icon等はOSが未ログイン状態で取得するため公開する）
  if (
    pathname.startsWith('/login') ||
    pathname.startsWith('/api/auth') ||
    pathname === '/apple-icon.png'
  ) {
    return NextResponse.next()
  }

  const token = req.cookies.get('auth_token')?.value
  const validToken = process.env.AUTH_TOKEN_VALUE

  if (!token || token !== validToken) {
    const loginUrl = req.nextUrl.clone()
    loginUrl.pathname = '/login'
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
