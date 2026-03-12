import '@testing-library/jest-dom'
import { beforeAll, afterEach, afterAll } from 'vitest'
import { server } from './__tests__/mocks/server'

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
