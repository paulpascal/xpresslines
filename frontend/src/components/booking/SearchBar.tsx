import { ActionIcon, Button, Group, Paper, Select, TextInput } from '@mantine/core';
import { IconArrowsLeftRight, IconSearch, IconX } from '@tabler/icons-react';

import type { Town } from '../../api/types';
import type { SearchCheck, SearchValues } from '../../lib/validation';

interface Props {
  towns: Town[];
  values: SearchValues;
  check: SearchCheck;
  minDate: string;
  loading: boolean;
  onChange: (values: SearchValues) => void;
  onSearch: () => void;
  onClear: () => void;
}

export function SearchBar({ towns, values, check, minDate, loading, onChange, onSearch, onClear }: Props) {
  const options = towns.map((t) => ({ value: t.code, label: `${t.name} (Zone ${t.zone})` }));
  const set = (patch: Partial<SearchValues>) => onChange({ ...values, ...patch });

  return (
    <Paper shadow="md" p="lg" radius="lg">
      <form onSubmit={(e) => { e.preventDefault(); if (check.canSearch) onSearch(); }}>
        <Group align="flex-start" grow preventGrowOverflow={false}>
          <Select label="From" placeholder="Choose a town" data={options} value={values.origin || null}
            clearable onChange={(v) => set({ origin: v ?? '' })} />
          <ActionIcon variant="light" size="lg" mt={25} style={{ flexGrow: 0 }} aria-label="Swap towns"
            onClick={() => set({ origin: values.destination, destination: values.origin })}>
            <IconArrowsLeftRight size={18} />
          </ActionIcon>
          <Select label="To" placeholder="Choose a town" data={options} value={values.destination || null}
            clearable onChange={(v) => set({ destination: v ?? '' })}
            error={check.sameTown ? 'Choose a town different from the origin' : undefined} />
          <TextInput label="Date" type="date" value={values.date} min={minDate}
            onChange={(e) => set({ date: e.currentTarget.value })}
            error={check.pastDate ? 'Pick today or a later date' : undefined} />
          <Button type="submit" color="gold" c="navy.9" leftSection={<IconSearch size={16} />}
            loading={loading} disabled={!check.canSearch} mt={25} style={{ flexGrow: 0 }}>
            Search trips
          </Button>
          <Button variant="default" leftSection={<IconX size={16} />} mt={25}
            disabled={check.isEmpty} onClick={onClear} style={{ flexGrow: 0 }}>
            Clear
          </Button>
        </Group>
      </form>
    </Paper>
  );
}
