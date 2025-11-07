import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const session = request.cookies.get('session');
  const pathname = request.nextUrl.pathname;
  console.log(session)

  // Permitir acceso libre al login
  if (pathname.startsWith('/login')) return NextResponse.next();

  // Si no hay sesión, redirigir al login
  if (!session) {
    const loginUrl = new URL('/login', request.url);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next|static|favicon.ico).*)'], // aplica a todo excepto archivos estáticos
};