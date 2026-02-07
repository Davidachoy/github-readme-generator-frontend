import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import ReactMarkdown from 'react-markdown'
import './App.css'
import {
  fetchProfile,
  generateReadme,
  type GeneratedReadme,
  type ProfileData,
  type ReadmeConfig,
} from './api'

type SectionKey = 'header' | 'stats' | 'languages' | 'repos' | 'badges' | 'charts'

const sectionLabels: Record<SectionKey, string> = {
  header: 'Header',
  stats: 'Stats',
  languages: 'Languages',
  repos: 'Repos',
  badges: 'Badges',
  charts: 'Charts',
}

const defaultSections: Record<SectionKey, boolean> = {
  header: true,
  stats: true,
  languages: true,
  repos: true,
  badges: false,
  charts: false,
}

const formatNumber = (value?: number) => {
  if (typeof value !== 'number') return 'n/a'
  return value.toLocaleString('en-US')
}

const formatBytes = (value?: number) => {
  if (typeof value !== 'number') return 'n/a'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = value
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex += 1
  }
  const precision = size < 10 && unitIndex > 0 ? 1 : 0
  return `${size.toFixed(precision)} ${units[unitIndex]}`
}

const getMarkdown = (result: GeneratedReadme | string) => {
  if (typeof result === 'string') return result
  return result.markdown ?? ''
}

const getAssets = (result: GeneratedReadme | string) => {
  if (typeof result === 'string') return null
  return result.assets ?? null
}

function App() {
  const [username, setUsername] = useState('')
  const [profile, setProfile] = useState<ProfileData | null>(null)
  const [profileLoading, setProfileLoading] = useState(false)
  const [profileError, setProfileError] = useState<string | null>(null)
  const [generateLoading, setGenerateLoading] = useState(false)
  const [generateError, setGenerateError] = useState<string | null>(null)
  const [markdown, setMarkdown] = useState('')
  const [assets, setAssets] = useState<Record<string, string> | null>(null)
  const [theme, setTheme] = useState('light')
  const [layout, setLayout] = useState('stacked')
  const [sections, setSections] = useState<Record<SectionKey, boolean>>(
    defaultSections,
  )
  const [copyStatus, setCopyStatus] = useState<string | null>(null)

  const trimmedUsername = username.trim()

  const selectedSections = useMemo(
    () =>
      Object.entries(sections)
        .filter(([, enabled]) => enabled)
        .map(([key]) => key),
    [sections],
  )

  const config: ReadmeConfig = useMemo(
    () => ({
      sections: selectedSections,
      theme,
      layout,
    }),
    [selectedSections, theme, layout],
  )

  const handleProfileSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!trimmedUsername) {
      setProfileError('Ingresa un username valido.')
      setProfile(null)
      return
    }
    setProfileLoading(true)
    setProfileError(null)
    try {
      const data = await fetchProfile(trimmedUsername)
      setProfile(data)
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Error al cargar perfil.'
      setProfile(null)
      setProfileError(message)
    } finally {
      setProfileLoading(false)
    }
  }

  const handleGenerate = async () => {
    if (!trimmedUsername) {
      setGenerateError('Ingresa un username valido.')
      return
    }
    setGenerateLoading(true)
    setGenerateError(null)
    setCopyStatus(null)
    try {
      const result = await generateReadme(trimmedUsername, config)
      const nextMarkdown = getMarkdown(result)
      if (!nextMarkdown) {
        setGenerateError('Respuesta sin markdown.')
        setMarkdown('')
        setAssets(null)
        return
      }
      setMarkdown(nextMarkdown)
      setAssets(getAssets(result))
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Error al generar README.'
      setGenerateError(message)
    } finally {
      setGenerateLoading(false)
    }
  }

  const handleCopy = async () => {
    if (!markdown) return
    if (!navigator.clipboard?.writeText) {
      setCopyStatus('Clipboard no disponible.')
      return
    }
    try {
      await navigator.clipboard.writeText(markdown)
      setCopyStatus('Copiado.')
      window.setTimeout(() => setCopyStatus(null), 1800)
    } catch {
      setCopyStatus('No se pudo copiar.')
    }
  }

  const handleDownload = () => {
    if (!markdown) return
    const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'README.md'
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  }

  const toggleSection = (key: SectionKey) => {
    setSections((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  const profileName = profile?.name || profile?.username || ''
  const profileBio = profile?.bio || 'Sin bio disponible.'
  const topLanguages = profile?.top_languages ?? []
  const repos = profile?.repos ?? []

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <p className="app-eyebrow">GitHub Profile README</p>
          <h1>Preview y export desde /api/profile y /api/generate</h1>
          <p className="app-subtitle">
            Consulta datos del perfil, configura secciones y genera Markdown.
          </p>
        </div>
        <div className="app-meta">
          <span className="meta-item">
            Endpoint perfil: <code>/api/profile</code>
          </span>
          <span className="meta-item">
            Endpoint generate: <code>/api/generate</code>
          </span>
        </div>
      </header>

      <div className="layout">
        <div className="left-column">
          <section className="panel">
            <div className="panel-header">
              <div>
                <h2>1. Perfil</h2>
                <p>Obtiene datos base desde GitHub.</p>
              </div>
            </div>
            <form className="form-row" onSubmit={handleProfileSubmit}>
              <div className="field">
                <label htmlFor="username">GitHub username</label>
                <input
                  id="username"
                  type="text"
                  placeholder="octocat"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                />
              </div>
              <button
                className="button primary"
                type="submit"
                disabled={!trimmedUsername || profileLoading}
              >
                {profileLoading ? 'Cargando...' : 'Cargar perfil'}
              </button>
            </form>
            {profileError && <p className="status error">{profileError}</p>}
            {profileLoading && <p className="status info">Buscando perfil...</p>}

            {!profile && !profileLoading && (
              <p className="status empty">
                Aun no hay perfil cargado. Usa el formulario para consultar uno.
              </p>
            )}

            {profile && (
              <div className="profile-card">
                <div className="profile-summary">
                  <h3>{profileName}</h3>
                  <p className="profile-username">@{profile.username}</p>
                  <p className="profile-bio">{profileBio}</p>
                </div>
                <div className="stats-grid">
                  <div>
                    <span>Followers</span>
                    <strong>{formatNumber(profile.followers)}</strong>
                  </div>
                  <div>
                    <span>Public repos</span>
                    <strong>{formatNumber(profile.public_repos)}</strong>
                  </div>
                </div>
                <div className="data-block">
                  <h4>Top languages</h4>
                  {topLanguages.length === 0 ? (
                    <p className="status empty">Sin datos de lenguajes.</p>
                  ) : (
                    <ul className="pill-list">
                      {topLanguages.map(([language, bytes]) => (
                        <li key={language}>
                          <span>{language}</span>
                          <strong>{formatBytes(bytes)}</strong>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                <div className="data-block">
                  <h4>Repos</h4>
                  {repos.length === 0 ? (
                    <p className="status empty">Sin repos destacados.</p>
                  ) : (
                    <ul className="repo-list">
                      {repos.map((repo) => (
                        <li key={repo.url}>
                          <div>
                            <a
                              href={repo.url}
                              target="_blank"
                              rel="noreferrer"
                            >
                              {repo.name}
                            </a>
                            {repo.description && (
                              <p className="repo-description">
                                {repo.description}
                              </p>
                            )}
                          </div>
                          <div className="repo-meta">
                            {repo.language && <span>{repo.language}</span>}
                            <span>Stars {formatNumber(repo.stars)}</span>
                            <span>Forks {formatNumber(repo.forks)}</span>
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            )}
          </section>

          <section className="panel">
            <div className="panel-header">
              <div>
                <h2>2. Configuracion</h2>
                <p>Selecciona tema, layout y secciones.</p>
              </div>
            </div>
            <div className="form-row">
              <div className="field">
                <label htmlFor="theme">Theme</label>
                <select
                  id="theme"
                  value={theme}
                  onChange={(event) => setTheme(event.target.value)}
                >
                  <option value="light">light</option>
                  <option value="dark">dark</option>
                  <option value="auto">auto</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="layout">Layout</label>
                <select
                  id="layout"
                  value={layout}
                  onChange={(event) => setLayout(event.target.value)}
                >
                  <option value="stacked">stacked</option>
                  <option value="two-column">two-column</option>
                  <option value="grid">grid</option>
                </select>
              </div>
            </div>
            <div className="sections-grid">
              {Object.entries(sectionLabels).map(([key, label]) => (
                <label className="checkbox" key={key}>
                  <input
                    type="checkbox"
                    checked={sections[key as SectionKey]}
                    onChange={() => toggleSection(key as SectionKey)}
                  />
                  <span>{label}</span>
                </label>
              ))}
            </div>
            <div className="actions">
              <button
                className="button primary"
                type="button"
                onClick={handleGenerate}
                disabled={!trimmedUsername || generateLoading}
              >
                {generateLoading ? 'Generando...' : 'Generar README'}
              </button>
              <button
                className="button secondary"
                type="button"
                onClick={() => {
                  setMarkdown('')
                  setAssets(null)
                  setGenerateError(null)
                }}
              >
                Limpiar preview
              </button>
            </div>
            {generateError && <p className="status error">{generateError}</p>}
            <div className="config-preview">
              <h3>Config enviada</h3>
              <pre>{JSON.stringify({ username: trimmedUsername, config }, null, 2)}</pre>
            </div>
          </section>
        </div>

        <section className="panel preview-panel">
          <div className="panel-header">
            <div>
              <h2>3. Previsualizacion</h2>
              <p>Resultado de la generacion en Markdown.</p>
            </div>
            <div className="toolbar">
              <button
                className="button ghost"
                type="button"
                onClick={handleCopy}
                disabled={!markdown}
              >
                Copiar
              </button>
              <button
                className="button ghost"
                type="button"
                onClick={handleDownload}
                disabled={!markdown}
              >
                Descargar
              </button>
            </div>
          </div>
          {copyStatus && <p className="status info">{copyStatus}</p>}
          <div className="preview-box">
            {markdown ? (
              <ReactMarkdown className="markdown-body">
                {markdown}
              </ReactMarkdown>
            ) : (
              <p className="status empty">
                Aun no hay markdown generado. Ejecuta la generacion.
              </p>
            )}
          </div>
          <div className="field">
            <label htmlFor="markdown">Markdown</label>
            <textarea id="markdown" readOnly rows={12} value={markdown} />
          </div>
          {assets && Object.keys(assets).length > 0 && (
            <div className="data-block">
              <h4>Assets</h4>
              <ul className="asset-list">
                {Object.entries(assets).map(([name, url]) => (
                  <li key={name}>
                    <span>{name}</span>
                    <a href={url} target="_blank" rel="noreferrer">
                      {url}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

export default App
