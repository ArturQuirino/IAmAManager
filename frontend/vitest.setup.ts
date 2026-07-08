import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

// Keep tests isolated and idempotent: unmount React trees and wipe the
// jsdom localStorage between tests so no state bleeds across them.
afterEach(() => {
  cleanup();
  localStorage.clear();
});
