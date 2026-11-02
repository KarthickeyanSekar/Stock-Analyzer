import {
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type Row,
  type SortingState,
} from '@tanstack/react-table';
import { ArrowDown, ArrowUp, ArrowUpDown, ChevronLeft, ChevronRight } from 'lucide-react';
import { useState, type ReactNode } from 'react';

import { cn } from '@/shared/lib/cn';
import { Button } from '@/shared/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';

declare module '@tanstack/react-table' {
  // Lets a column ask for right-aligned (numeric) cells: ``meta: { align: 'right' }``.
  // The type parameters must match TanStack's declaration to merge with it.
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  interface ColumnMeta<TData, TValue> {
    align?: 'right';
  }
}

const PAGE_SIZES = [10, 25, 50];

interface DataTableProps<T> {
  data: T[];
  columns: ColumnDef<T>[];
  /** Initial sort, e.g. ``[{ id: 'probability', desc: true }]``. */
  initialSorting?: SortingState;
  /** Text typed in an external search box; matched by ``matches``. */
  search?: string;
  matches?: (row: T, search: string) => boolean;
  /** Phone layout: one card per row (the table is shown from ``md`` up). */
  renderCard?: (row: Row<T>) => ReactNode;
  getRowId: (row: T) => string;
  label: string;
  /** Shown instead of the table when nothing matches (icon + sentence + action). */
  empty?: ReactNode;
}

/** Sortable, filterable, paginated table (TanStack Table) styled with the design tokens. */
export function DataTable<T>({
  data,
  columns,
  initialSorting = [],
  search = '',
  matches,
  renderCard,
  getRowId,
  label,
  empty,
}: DataTableProps<T>) {
  const [sorting, setSorting] = useState<SortingState>(initialSorting);
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: PAGE_SIZES[1] ?? 25 });
  // TanStack Table returns functions that change on each render; the React Compiler can't memoise it.
  // eslint-disable-next-line react-hooks/incompatible-library
  const table = useReactTable({
    data,
    columns,
    getRowId,
    state: { sorting, pagination, globalFilter: search },
    onSortingChange: setSorting,
    onPaginationChange: setPagination,
    globalFilterFn: (row, _columnId, value: string) =>
      !value || !matches || matches(row.original, value.trim().toLowerCase()),
    autoResetPageIndex: true,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });
  const rows = table.getRowModel().rows;
  const total = table.getFilteredRowModel().rows.length;
  const { pageIndex, pageSize } = table.getState().pagination;
  const first = total === 0 ? 0 : pageIndex * pageSize + 1;
  const last = Math.min(total, (pageIndex + 1) * pageSize);

  if (total === 0 && empty) return <>{empty}</>;

  return (
    <div className="flex flex-col gap-3">
      <div className="hidden overflow-x-auto rounded-xl border bg-card md:block">
        <table className="w-full text-sm" aria-label={label}>
          <thead className="text-xs text-muted-foreground">
            {table.getHeaderGroups().map((group) => (
              <tr key={group.id} className="border-b">
                {group.headers.map((header) => {
                  const sorted = header.column.getIsSorted();
                  const align = header.column.columnDef.meta?.align;
                  return (
                    <th
                      key={header.id}
                      aria-sort={
                        sorted === 'asc' ? 'ascending' : sorted === 'desc' ? 'descending' : 'none'
                      }
                      className={cn(
                        'px-4 py-2 font-medium',
                        align === 'right' ? 'text-right' : 'text-left',
                      )}
                    >
                      {header.column.getCanSort() ? (
                        <button
                          type="button"
                          onClick={header.column.getToggleSortingHandler()}
                          className={cn(
                            'inline-flex min-h-8 items-center gap-1 rounded hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none',
                            sorted && 'text-foreground',
                          )}
                        >
                          {flexRender(header.column.columnDef.header, header.getContext())}
                          {sorted === 'asc' ? (
                            <ArrowUp className="size-3.5" aria-hidden="true" />
                          ) : sorted === 'desc' ? (
                            <ArrowDown className="size-3.5" aria-hidden="true" />
                          ) : (
                            <ArrowUpDown className="size-3.5 opacity-50" aria-hidden="true" />
                          )}
                        </button>
                      ) : (
                        flexRender(header.column.columnDef.header, header.getContext())
                      )}
                    </th>
                  );
                })}
              </tr>
            ))}
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-b last:border-0 hover:bg-muted/60">
                {row.getVisibleCells().map((cell) => {
                  const align = cell.column.columnDef.meta?.align;
                  return (
                    <td
                      key={cell.id}
                      className={cn('px-4 py-2', align === 'right' && 'text-right')}
                    >
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {renderCard && <ul className="grid gap-2 md:hidden">{rows.map((row) => renderCard(row))}</ul>}

      <nav
        className="flex flex-wrap items-center justify-between gap-3 text-sm text-muted-foreground"
        aria-label={`${label} pages`}
      >
        <span aria-live="polite">
          {first}–{last} of {total}
        </span>
        <div className="flex items-center gap-2">
          <Select
            value={String(pageSize)}
            onValueChange={(value) => {
              table.setPageSize(Number(value ?? pageSize));
            }}
          >
            <SelectTrigger className="h-9 w-28" aria-label="Rows per page">
              <SelectValue>{(value: string) => `${value} / page`}</SelectValue>
            </SelectTrigger>
            <SelectContent>
              {PAGE_SIZES.map((size) => (
                <SelectItem key={size} value={String(size)}>
                  {size} / page
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="icon"
            className="size-9"
            aria-label="Previous page"
            disabled={!table.getCanPreviousPage()}
            onClick={() => {
              table.previousPage();
            }}
          >
            <ChevronLeft aria-hidden="true" />
          </Button>
          <span>
            Page {pageIndex + 1} of {Math.max(1, table.getPageCount())}
          </span>
          <Button
            variant="outline"
            size="icon"
            className="size-9"
            aria-label="Next page"
            disabled={!table.getCanNextPage()}
            onClick={() => {
              table.nextPage();
            }}
          >
            <ChevronRight aria-hidden="true" />
          </Button>
        </div>
      </nav>
    </div>
  );
}
