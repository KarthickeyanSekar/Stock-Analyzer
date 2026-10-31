import createClient from 'openapi-fetch';

import type { paths } from './schema';

/** Typed API client generated from the backend's OpenAPI schema (`npm run api-client`). */
export const apiClient = createClient<paths>({ baseUrl: '/' });
