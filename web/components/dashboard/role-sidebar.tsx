"use client";

import type { ComponentType } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bot,
  BriefcaseBusiness,
  CalendarDays,
  ClipboardList,
  FileCheck2,
  FileText,
  FolderKanban,
  LayoutDashboard,
  MessageSquareText,
  PackageCheck,
  ScrollText,
  ShieldCheck,
  UserRound,
  UsersRound,
} from "lucide-react";

import { roleLabel } from "@/lib/formatters";
import type { AuthUser, UserRole } from "@/types/auth";

type NavigationItem = {
  href: string;
  label: string;
  roles: UserRole[];
  icon: ComponentType<{ className?: string }>;
};

const navigationItems: NavigationItem[] = [
  {
    href: "/dashboard",
    icon: LayoutDashboard,
    label: "Bảng điều khiển",
    roles: ["ADMIN", "EMPLOYEE", "CUSTOMER"],
  },
  {
    href: "/dashboard/admin/users",
    icon: ShieldCheck,
    label: "Người dùng",
    roles: ["ADMIN"],
  },
  {
    href: "/dashboard/admin/employees",
    icon: BriefcaseBusiness,
    label: "Nhân viên",
    roles: ["ADMIN"],
  },
  {
    href: "/dashboard/admin/customers",
    icon: UsersRound,
    label: "Khách hàng",
    roles: ["ADMIN"],
  },
  {
    href: "/dashboard/admin/assignments",
    icon: FolderKanban,
    label: "Phân công",
    roles: ["ADMIN"],
  },
  {
    href: "/dashboard/admin/subscriptions",
    icon: FileCheck2,
    label: "Hợp đồng bảo hiểm",
    roles: ["ADMIN"],
  },
  {
    href: "/dashboard/admin/claims",
    icon: ClipboardList,
    label: "Hồ sơ bồi thường",
    roles: ["ADMIN"],
  },
  {
    href: "/dashboard/admin/appointments",
    icon: CalendarDays,
    label: "Lịch hẹn",
    roles: ["ADMIN"],
  },
  {
    href: "/dashboard/admin/documents",
    icon: FileText,
    label: "Tài liệu AI",
    roles: ["ADMIN"],
  },
  {
    href: "/dashboard/admin/insurance/packages",
    icon: PackageCheck,
    label: "Gói bảo hiểm",
    roles: ["ADMIN"],
  },
  {
    href: "/dashboard/admin/insurance/processes",
    icon: ScrollText,
    label: "Quy trình bảo hiểm",
    roles: ["ADMIN"],
  },
  {
    href: "/dashboard/employee/customers",
    icon: UsersRound,
    label: "Khách hàng phụ trách",
    roles: ["EMPLOYEE"],
  },
  {
    href: "/dashboard/employee/claims",
    icon: ClipboardList,
    label: "Xử lý bồi thường",
    roles: ["EMPLOYEE"],
  },
  {
    href: "/dashboard/employee/chat",
    icon: MessageSquareText,
    label: "Trò chuyện",
    roles: ["EMPLOYEE"],
  },
  {
    href: "/dashboard/employee/appointments",
    icon: CalendarDays,
    label: "Lịch hẹn",
    roles: ["EMPLOYEE"],
  },
  {
    href: "/dashboard/customer/profile",
    icon: UserRound,
    label: "Hồ sơ của tôi",
    roles: ["CUSTOMER"],
  },
  {
    href: "/dashboard/customer/subscriptions",
    icon: FileCheck2,
    label: "Hợp đồng bảo hiểm",
    roles: ["CUSTOMER"],
  },
  {
    href: "/dashboard/customer/claims",
    icon: ClipboardList,
    label: "Hồ sơ bồi thường",
    roles: ["CUSTOMER"],
  },
  {
    href: "/dashboard/customer/report-incident",
    icon: FileText,
    label: "Báo cáo sự cố",
    roles: ["CUSTOMER"],
  },
  {
    href: "/dashboard/customer/chat",
    icon: MessageSquareText,
    label: "Trò chuyện",
    roles: ["CUSTOMER"],
  },
  {
    href: "/dashboard/customer/appointments",
    icon: CalendarDays,
    label: "Lịch hẹn của tôi",
    roles: ["CUSTOMER"],
  },
  {
    href: "/dashboard/customer/book-appointment",
    icon: CalendarDays,
    label: "Đặt lịch hẹn",
    roles: ["CUSTOMER"],
  },
  {
    href: "/dashboard/customer/chatbot",
    icon: Bot,
    label: "Trợ lý bảo hiểm AI",
    roles: ["CUSTOMER"],
  },
];

export function RoleSidebar({ user }: { user: AuthUser }) {
  const pathname = usePathname();
  const items = navigationItems.filter((item) => item.roles.includes(user.role));
  const displayName =
    user.full_name === "System Administrator"
      ? "Quản trị viên hệ thống"
      : user.full_name;

  return (
    <aside className="hidden border-r border-border bg-white/95 p-5 lg:block">
      <Link className="flex items-center gap-3 text-lg font-extrabold" href="/">
        <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-white">
          <ShieldCheck aria-hidden className="h-5 w-5" />
        </span>
        Bảo hiểm Việt
      </Link>
      <div className="mt-6 rounded-lg border border-border bg-mist p-4">
        <p className="text-sm font-bold text-ink">{displayName}</p>
        <p className="mt-1 text-xs font-semibold text-primary">
          {roleLabel(user.role)}
        </p>
      </div>
      <nav
        aria-label="Điều hướng chính"
        className="mt-8 space-y-1 text-sm font-semibold text-slate-600"
      >
        {items.map((item) => {
          const isActive =
            pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;
          return (
            <Link
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 transition ${
                isActive
                  ? "bg-primary text-white shadow-sm"
                  : "hover:bg-slate-100 hover:text-ink"
              }`}
              href={item.href}
              key={item.href}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
