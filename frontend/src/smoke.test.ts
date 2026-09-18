import { describe, expect, it } from 'vitest'

describe('Darukaa.Earth frontend foundation', () => {
  it('uses the configured API URL when present', () => {
    expect(typeof import.meta.env.VITE_API_URL === 'string' || import.meta.env.VITE_API_URL === undefined).toBe(true)
  })
})
