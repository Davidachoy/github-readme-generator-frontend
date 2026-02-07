export type ProfileRepo = {
  name: string
  url: string
  description?: string | null
  stars?: number
  forks?: number
  language?: string | null
}

export type ProfileData = {
  username: string
  name?: string | null
  bio?: string | null
  followers?: number
  public_repos?: number
  top_languages: [string, number][]
  repos: ProfileRepo[]
}

export type ReadmeConfig = {
  sections: string[]
  theme: string
  layout: string
  template?: string
}

export type GeneratedReadme = {
  markdown?: string
  assets?: Record<string, string>
}

const apiBase = ''

const readErrorMessage = async (res: Response) => {
  const contentType = res.headers.get('content-type') ?? ''
  if (contentType.includes('application/json')) {
    try {
      const data = await res.json()
      if (typeof data?.detail === 'string') {
        return data.detail
      }
      return JSON.stringify(data)
    } catch {
      return `Request failed (${res.status})`
    }
  }
  try {
    const text = await res.text()
    return text || `Request failed (${res.status})`
  } catch {
    return `Request failed (${res.status})`
  }
}

export const fetchProfile = async (username: string): Promise<ProfileData> => {
  const res = await fetch(`${apiBase}/api/profile/${encodeURIComponent(username)}`)
  if (!res.ok) {
    throw new Error(await readErrorMessage(res))
  }
  return (await res.json()) as ProfileData
}

export const generateReadme = async (
  username: string,
  config: ReadmeConfig,
): Promise<GeneratedReadme> => {
  const res = await fetch(`${apiBase}/api/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, config }),
  })
  if (!res.ok) {
    throw new Error(await readErrorMessage(res))
  }
  const contentType = res.headers.get('content-type') ?? ''
  if (!contentType.includes('application/json')) {
    const text = await res.text()
    throw new Error(
      `El servidor devolvió ${contentType || 'respuesta vacía'} en lugar de JSON. ¿Está el backend en marcha en el puerto 8000?`,
    )
  }
  return (await res.json()) as GeneratedReadme
}
