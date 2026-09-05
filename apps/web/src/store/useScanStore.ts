import { create } from 'zustand';
import { Finding } from '../types';

interface ScanState {
  selectedFinding: Finding | null;
  selectFinding: (finding: Finding | null) => void;
}

export const useScanStore = create<ScanState>((set) => ({
  selectedFinding: null,
  selectFinding: (finding: Finding | null) => {
    set({ selectedFinding: finding });
  },
}));
