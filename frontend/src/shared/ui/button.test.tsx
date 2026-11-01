import { fireEvent, render, screen } from '@testing-library/react';
import { Plus } from 'lucide-react';
import { describe, expect, it, vi } from 'vitest';

import { Button } from './button';

describe('Button (shadcn/ui)', () => {
  it('renders with its label and handles clicks', () => {
    const onClick = vi.fn();
    render(
      <Button onClick={onClick}>
        <Plus /> Start plan
      </Button>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Start plan' }));

    expect(onClick).toHaveBeenCalledOnce();
  });

  it('does not fire when disabled', () => {
    const onClick = vi.fn();
    render(
      <Button disabled onClick={onClick}>
        Close plan
      </Button>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Close plan' }));

    expect(onClick).not.toHaveBeenCalled();
  });

  it('applies the variant styles from tokens', () => {
    render(<Button variant="outline">Cancel</Button>);

    expect(screen.getByRole('button', { name: 'Cancel' }).className).toMatch(/border-border/);
  });
});
