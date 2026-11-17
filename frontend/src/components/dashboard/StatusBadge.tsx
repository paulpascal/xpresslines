import { Badge } from '@mantine/core';

import type { TripStatus } from '../../api/types';
import { STATUS_LABELS } from '../../lib/format';

const COLORS: Record<TripStatus, string> = {
  scheduled: 'navy',
  boarding: 'gold',
  departed: 'violet',
  in_transit: 'cyan',
  arrived: 'teal',
  completed: 'gray',
};

export function StatusBadge({ status }: { status: TripStatus }) {
  return (
    <Badge color={COLORS[status]} variant="light" radius="sm">
      {STATUS_LABELS[status]}
    </Badge>
  );
}
