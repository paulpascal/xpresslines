import { Alert, Container, Pagination, SegmentedControl, SimpleGrid, Stack, Text, Title } from '@mantine/core';

import { StatCard } from '../components/dashboard/StatCard';
import { TripsTable } from '../components/dashboard/TripsTable';
import { REFRESH_MS, useDashboard } from '../hooks/useDashboard';
import type { StatusFilter } from '../lib/dashboard';
import { STATUS_LABELS } from '../lib/format';

const FILTERS = [{ value: 'all', label: 'All' }, ...Object.entries(STATUS_LABELS).map(([value, label]) => ({ value, label }))];

/** Operator view: the hook holds the state and logic; this file only arranges the components. */
export function DashboardPage() {
  const board = useDashboard();
  const { stats } = board;

  return (
    <Container size="lg" py="xl">
      <Stack>
        <div>
          <Title order={2}>Operations dashboard</Title>
          <Text c="dimmed" size="sm">
            All trips, soonest first, refreshed every {REFRESH_MS / 1000} seconds. Times are Lagos time.
          </Text>
        </div>

        <SimpleGrid cols={4}>
          <StatCard label="Trips" value={board.total} />
          <StatCard label="Seats sold" value={stats.seatsSold} />
          <StatCard label="Load factor" value={stats.loadFactorPercent === null ? '-' : `${stats.loadFactorPercent}%`} />
          <StatCard label="On the road" value={stats.onTheRoad} />
        </SimpleGrid>

        <div>
          <Text size="sm" fw={700} mb={6}>Filter by status</Text>
          <SegmentedControl color="navy" size="md" fullWidth withItemsBorders={false} data={FILTERS} value={board.filter}
            onChange={(v) => board.setFilter(v as StatusFilter)} />
        </div>
        {board.error && <Alert color="red">{board.error}</Alert>}

        <TripsTable trips={board.visibleTrips} busyTripId={board.busyTripId} onAdvance={board.advance} />
        {board.pageCount > 1 && (
          <Pagination total={board.pageCount} value={board.pageNumber} onChange={board.setPageNumber}
            style={{ alignSelf: 'center' }} />
        )}
      </Stack>
    </Container>
  );
}
