import type { FormEventHandler, ReactNode } from "react";
import { Search } from "lucide-react";

type SearchFilterBarProps = {
  children?: ReactNode;
  onSubmit?: FormEventHandler<HTMLFormElement>;
  search: string;
  searchPlaceholder?: string;
  setSearch: (value: string) => void;
};

export function SearchFilterBar({
  children,
  onSubmit,
  search,
  searchPlaceholder = "Tìm kiếm",
  setSearch,
}: SearchFilterBarProps) {
  return (
    <form
      className="flex flex-col gap-3 rounded-lg border border-border bg-white p-3 shadow-sm lg:flex-row lg:items-center"
      onSubmit={onSubmit}
    >
      <label className="relative min-w-64 flex-1">
        <span className="sr-only">{searchPlaceholder}</span>
        <Search
          aria-hidden
          className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted"
        />
        <input
          className="w-full rounded-md border border-border bg-white py-2 pl-9 pr-3 text-sm text-ink outline-none transition focus:border-primary focus:ring-2 focus:ring-blue-100"
          onChange={(event) => setSearch(event.target.value)}
          placeholder={searchPlaceholder}
          value={search}
        />
      </label>
      {children}
    </form>
  );
}
