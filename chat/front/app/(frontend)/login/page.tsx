'use client';

import { loginAction } from '@/app/actions/login';
import { LogoUTP } from '@/app/components/logos/utp';
import { useState } from 'react';
import { useFormStatus } from 'react-dom';

export default function LoginPage() {
  const [error, setError] = useState('');
  const { pending } = useFormStatus();

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError('');
    const formData = new FormData(e.currentTarget);
    const res = await loginAction(formData);
    if (!res.success) setError(res.message as string);
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#fff]">
      <div className="bg-white rounded-2xl shadow-lg w-full max-w-md p-8">
        <div className="flex justify-center mb-6">
          <LogoUTP />
        </div>


        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-gray-700 text-sm font-medium mb-1">
              Correo institucional
            </label>
            <input
              name="email"
              type="email"
              required
              className="text-[#000] w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#d3052d]"
              placeholder="tucorreo@utp.edu.pe"
            />
          </div>

          <div>
            <label className="block text-gray-700 text-sm font-medium mb-1">
              Contraseña
            </label>
            <input
              name="password"
              type="password"
              required
              className="text-[#000] w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#d3052d]"
              placeholder="••••••••"
            />
          </div>

          {error && (
            <p className="text-sm text-red-600 text-center">{error}</p>
          )}

          <button
            type="submit"
            disabled={pending}
            className="w-full bg-[#d3052d] hover:bg-[#b20424] text-white font-semibold py-2 rounded-lg transition cursor-pointer disabled:opacity-50"
          >
            {pending ? 'Ingresando...' : 'Ingresar'}
          </button>
        </form>
      </div>
    </div>
  );
}