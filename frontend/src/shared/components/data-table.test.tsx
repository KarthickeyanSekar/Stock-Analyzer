import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { type ColumnDef } from '@tanstack/react-table';
import { afterEach, describe, expect, it } from 'vitest';

import { DataTable } from './data-table';

interface Item {
  name: string;
  value: number;
}

const items: Item[] = Array.from({ length: 30 }, (_, i) => ({
  name: `Item ${String(i + 1)}`,
  value: i % 7,
}));
const columns: ColumnDef<Item>[] = [
  { id: 'name', header: 'Name', accessorFn: (row) => row.name },
  { id: 'value', header: 'Value', accessorFn: (row) => row.value, meta: { align: 'right' } },
];

function renderTable(search = '') {
  return render(
    <DataTable
      label="Items"
      data={items}
      columns={columns}
      search={search}
      matches={(row, text) => row.name.toLowerCase().includes(text)}
      getRowId={(row) => row.name}
    />,
  );
}

const bodyRows = () => within(screen.getByRole('table')).getAllByRole('row').slice(1);

afterEach(cleanup);

describe('DataTable', () => {
  it('paginates 25 rows per page', () => {
    renderTable();

    expect(bodyRows()).toHaveLength(25);
    expect(screen.getByText('1–25 of 30')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Next page' }));
    expect(bodyRows()).toHaveLength(5);
    expect(screen.getByText('Page 2 of 2')).toBeInTheDocument();
  });

  it('sorts by a column and reports it to assistive tech', () => {
    renderTable();
    const header = screen.getByRole('columnheader', { name: /Value/ });

    // Numbers sort highest first on the first click (best chance first), then lowest first.
    fireEvent.click(within(header).getByRole('button'));
    expect(header).toHaveAttribute('aria-sort', 'descending');
    expect(within(bodyRows()[0] as HTMLElement).getAllByRole('cell')[1]).toHaveTextContent('6');
    fireEvent.click(within(header).getByRole('button'));
    expect(header).toHaveAttribute('aria-sort', 'ascending');
    expect(within(bodyRows()[0] as HTMLElement).getAllByRole('cell')[1]).toHaveTextContent('0');
  });

  it('filters with the search text', () => {
    renderTable('item 3');

    const names = bodyRows().map((row) => within(row).getAllByRole('cell')[0]?.textContent);
    expect(names).toEqual(['Item 3', 'Item 30']);
    expect(screen.getByText('1–2 of 2')).toBeInTheDocument();
  });
});
