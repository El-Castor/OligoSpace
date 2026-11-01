export function startJobPolling(refresh: () => void, onLimit: () => void, schedule: (tick: () => void, delay: number) => () => void): () => void {
  let refreshes = 0;
  let stopped = false;
  const cancel = schedule(() => {
    if (stopped) return;
    refreshes += 1;
    refresh();
    if (refreshes >= 40) { stopped = true; cancel(); onLimit(); }
  }, 1500);
  return () => { stopped = true; cancel(); };
}
