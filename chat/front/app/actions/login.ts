'use server';

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export async function loginAction(formData: FormData) {
  const email = formData.get('email') as string;
  const password = formData.get('password') as string;

  // Simulación de autenticación (puedes reemplazar con tu API real)
  if (email === 'admin@utp.edu.pe' && password === '123456') {
    const cookieStore = await cookies();
    // Guarda cookie de sesión
    cookieStore.set('session', 'true', {
      httpOnly: true,
      path: '/',
      maxAge: 60 * 60 * 4, // 4 horas
    });

    redirect('/'); // Redirige a la raíz
  }

  return { success: false, message: 'Credenciales incorrectas' };
}

export async function logoutAction() {
    const cookieStore = await cookies();
    cookieStore.delete('session');
    redirect('/login');
}