import { http, HttpResponse } from 'msw';

export const handlers = [
  http.post('/api/auth/jwt/login', async ({ request }) => {
    const body = await request.text();
    const params = new URLSearchParams(body);
    const password = params.get('password');

    if (password === 'wrongpassword') {
      return HttpResponse.json({ detail: 'LOGIN_BAD_CREDENTIALS' }, { status: 400 });
    }
    return HttpResponse.json({ access_token: 'fake-token', token_type: 'bearer' });
  }),

  http.post('/api/auth/register', async ({ request }) => {
    const body = await request.json() as { email: string; password: string };

    if (body.email === 'existing@test.com') {
      return HttpResponse.json({ detail: 'REGISTER_USER_ALREADY_EXISTS' }, { status: 400 });
    }
    return HttpResponse.json({ id: 1, email: body.email }, { status: 201 });
  }),

  http.post('/api/auth/jwt/logout', () => {
    return new HttpResponse(null, { status: 200 });
  }),
];
