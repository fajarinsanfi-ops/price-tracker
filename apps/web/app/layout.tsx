import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "Price Tracker — Personal Dashboard", description: "Monitor product prices and receive WhatsApp price-drop alerts." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="id"><body>{children}</body></html>; }
