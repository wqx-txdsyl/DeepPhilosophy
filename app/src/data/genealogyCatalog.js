import { ossImg } from './ossUrls.js';

function validateCatalog(data) {
  if (!Array.isArray(data) || data.length === 0) throw new Error('Empty genealogy catalog');
  const ids = new Set();
  for (const school of data) {
    if (typeof school.id !== 'string' || ids.has(school.id) || typeof school.name !== 'string' || typeof school.century !== 'string' || !Array.isArray(school.thinkers) || typeof school.image !== 'string' || !school.image.startsWith('/schools/')) throw new Error('Invalid genealogy catalog');
    ids.add(school.id);
  }
  return data;
}

export async function loadGenealogyCatalog(signal) {
  for (const url of [ossImg('/gene/atlas.json'), '/gene/atlas.json']) {
    try {
      const response = await fetch(url, { signal, cache: 'no-cache' });
      if (!response.ok) throw new Error('Genealogy catalog request failed');
      return validateCatalog(await response.json());
    } catch (error) {
      if (signal?.aborted) throw error;
    }
  }
  throw new Error('Genealogy catalog unavailable');
}
