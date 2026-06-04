import Link from "next/link";

export default function Navbar() {
  return (
    <nav className="border-b border-gray-200 bg-white">
      <div className="mx-auto max-w-6xl px-4 h-14 flex items-center justify-between">
        <Link href="/" className="text-lg font-bold text-gray-900">
          API Sentinel
        </Link>
        <Link
          href="/settings"
          className="text-sm text-gray-600 hover:text-gray-900"
        >
          Settings
        </Link>
      </div>
    </nav>
  );
}
