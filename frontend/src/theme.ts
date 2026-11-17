import { createTheme, type MantineColorsTuple } from '@mantine/core';

const navy: MantineColorsTuple = [
  '#eef3fb', '#d9e2f1', '#aec2e3', '#809fd5', '#5a82c9', '#426fc2',
  '#3465c0', '#2654a9', '#1d4a98', '#0f2a54',
];
const gold: MantineColorsTuple = [
  '#fff8e1', '#ffefcc', '#ffdd9b', '#ffca64', '#ffba38', '#ffb01b',
  '#ffab09', '#e39500', '#ca8400', '#af7100',
];

// Bundled with the app (see main.tsx), never loaded from a CDN, so it works offline.
const FONT = "'Manrope Variable', system-ui, sans-serif";

export const theme = createTheme({
  primaryColor: 'navy',
  colors: { navy, gold },
  fontFamily: FONT,
  headings: { fontFamily: FONT, fontWeight: '700' },
  defaultRadius: 'md',
});
