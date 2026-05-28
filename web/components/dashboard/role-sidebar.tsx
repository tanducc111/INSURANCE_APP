"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import type { AuthUser, UserRole } from "@/types/auth";

type NavigationItem = {
  href: string;
  label: string;
  roles: UserRole[];
};

const navigationItems: NavigationItem[] = [
  {
    href: "/dashboard",
    label: "Overview",
    roles: ["ADMIN", "EMPLOYEE", "CUSTOMER"],
  },
  {
    href: "/dashboard/admin/users",
    label: "User Management",
    roles: ["ADMIN"],
  },
  {
    href: "/dashboard/admin/insurance/packages",
    label: "Insurance Packages",
    roles: ["ADMIN"],
  },
  {
    href: "/dashboard/admin/insurance/processes",
    label: "Insurance Processes",
    roles: ["ADMIN"],
  },
];

export function RoleSidebar({ user }: { user: AuthUser }) {
  const pathname = usePathname();
  const items = navigationItems.filter((item) => item.roles.includes(user.role));

  return (
    <aside className="border-r border-slate-200 bg-white p-5">
      <Link className="text-lg font-semibold" href="/">
        Insurance Management
      </Link>
      <div className="mt-5 rounded-md border border-slate-200 bg-mist p-3">
        <p className="text-sm font-semibold">{user.full_name}</p>
        <p className="mt-1 text-xs font-medium text-ocean">{user.role}</p>
      </div>
      <nav className="mt-8 space-y-2 text-sm font-medium text-slate-600">
        {items.map((item) => {
          const isActive =
            pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              className={`block rounded-md px-3 py-2 transition ${
                isActive
                  ? "bg-ocean text-white"
                  : "hover:bg-slate-100 hover:text-ink"
              }`}
              href={item.href}
              key={item.href}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
