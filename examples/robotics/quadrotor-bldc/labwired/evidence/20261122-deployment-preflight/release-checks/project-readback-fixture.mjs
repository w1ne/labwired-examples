/** Existing project loader fixture for an isolated anonymous smoke page.
 * The caller supplies the authorized, hash-checked readback; no session is read.
 * Every route override is returned for the test receipt. Runtime/ELF traffic is real.
 */
export async function installProjectReadbackFixture(page, response) {
  const project = response.project;
  if (!project?.id || !project.content_hash || typeof project.diagram_json !== 'string') {
    throw new Error('Expected the checked project response fixture');
  }
  const url = `https://api.labwired.com/v1/projects/${encodeURIComponent(project.id)}`;
  const requests = [];
  await page.route(url, async route => {
    const method = route.request().method();
    requests.push({ url: route.request().url(), method });
    if (method !== 'GET') { await route.abort(); throw new Error('Unexpected write to the fixture project'); }
    await route.fulfill({ status: 200, contentType: 'application/json',
      headers: { 'access-control-allow-origin': 'https://app.labwired.com' },
      body: JSON.stringify(response) });
  });
  return { kind: 'authorized-readback-project-load-fixture', requests,
    overrides: [{ method: 'GET', url, contentHash: project.content_hash }],
    signedInProjectFetchObserved: false };
}
