import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "UTP | Bot Conversacional",
  description: "Asistente virtual para la Universidad Tecnológica de Peru.",
  icons: {
    icon: 'https://www.utp.edu.pe/sites/default/files/favicon_utp_1.png',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={` antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
