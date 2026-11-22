/** Passive observer for the repository's existing browser smoke harness.
 * No browser launch, credentials, engine stepping, input injection or clock override.
 * Install before normal navigation; drive Run/Pause through the existing UI harness.
 */
export async function installPassiveFlightCapture(page) {
  await page.addInitScript(() => {
    const capture = { schema: 'labwired.flight-capture/v1', events: [], overflow: 0, errors: [] };
    Object.defineProperty(window, '__LABWIRED_FLIGHT_CAPTURE__', { value: capture, configurable: true });
    window.addEventListener('labwired:flight-observation', event => {
      if (event.detail?.schema !== 'labwired.flight-observation/v1') return;
      if (capture.events.length >= 750_000) { capture.overflow++; return; }
      try { capture.events.push(JSON.parse(JSON.stringify(event.detail))); }
      catch (error) { capture.errors.push(String(error)); }
    });
  });
}

/** Reads only. The caller owns its cursor and persists every returned event. */
export async function readPassiveFlightCapture(page, cursor = 0, limit = 5000) {
  return page.evaluate(({ cursor, limit }) => {
    const capture = window.__LABWIRED_FLIGHT_CAPTURE__;
    if (!capture) return { available: false };
    let worldHealth = null;
    try { worldHealth = window.__LABWIRED_SMOKE__?.worldHealth?.() ?? null; } catch { /* reported below */ }
    return { available: true, schema: capture.schema, total: capture.events.length,
      cursor, events: capture.events.slice(cursor, cursor + limit),
      overflow: capture.overflow, errors: capture.errors.slice(), worldHealth,
      status: document.querySelector('[aria-label="System simulation controls"]')?.getAttribute('data-status') ?? null };
  }, { cursor, limit });
}
