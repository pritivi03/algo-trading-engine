import { NavLink } from "react-router-dom";
import type { ReactNode } from "react";

const navItems = [
  { to: "/sessions", label: "Sessions" },
  { to: "/strategies", label: "Strategies" },
];

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen">
      <aside className="w-52 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="px-5 py-6 border-b border-gray-800">
          <span className="text-sm font-semibold text-gray-400 uppercase tracking-widest">
            Algo Engine
          </span>
        </div>
        <nav className="flex flex-col gap-1 p-3 flex-1">
          {navItems.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-indigo-600 text-white"
                    : "text-gray-400 hover:text-gray-100 hover:bg-gray-800"
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1 overflow-auto p-8">{children}</main>
    </div>
  );
}