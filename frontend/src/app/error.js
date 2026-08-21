'use client'; // Error components must be Client Components

import { useEffect } from 'react';

export default function Error({ error, reset }) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error('Global Error Boundary Caught:', error);
  }, [error]);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
      <div className="bg-white p-8 md:p-12 rounded-3xl shadow-2xl border border-rose-100 text-center max-w-md w-full">
        <div className="w-20 h-20 bg-rose-50 text-rose-500 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
          </svg>
        </div>
        <h2 className="text-2xl font-bold text-slate-900 mb-2">Eyvah, Bir Şeyler Ters Gitti!</h2>
        <p className="text-slate-500 mb-8 text-sm leading-relaxed">
          Uygulama çalışırken beklenmedik bir hatayla karşılaştık. Ancak endişelenmeyin, verileriniz güvende. Sayfayı yenileyerek baştan başlayabilirsiniz.
        </p>
        <button
          onClick={
            // Attempt to recover by trying to re-render the segment
            () => reset()
          }
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-xl transition duration-200 shadow-lg shadow-blue-600/30"
        >
          Tekrar Dene
        </button>
      </div>
      
      <footer className="mt-12 text-center text-slate-400">
        <p className="text-sm font-medium">© 2026 Değerinde. Tüm hakları saklıdır.</p>
      </footer>
    </div>
  );
}
