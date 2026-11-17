import '@fontsource-variable/manrope';
import './global.css';
import '@mantine/core/styles.css';

import { MantineProvider } from '@mantine/core';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import { Layout, type Page } from './components/layout/Layout';
import { BookingPage } from './pages/BookingPage';
import { DashboardPage } from './pages/DashboardPage';
import { theme } from './theme';

// Two views, so a full router would be overkill: the path picks the page.
const page: Page = window.location.pathname.startsWith('/admin') ? 'admin' : 'book';
const PAGES = { book: BookingPage, admin: DashboardPage };
const Current = PAGES[page];

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <MantineProvider theme={theme}>
      <Layout active={page}>
        <Current />
      </Layout>
    </MantineProvider>
  </StrictMode>,
);
