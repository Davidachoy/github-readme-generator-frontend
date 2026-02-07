import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import ReactMarkdown from 'react-markdown'
import rehypeRaw from 'rehype-raw'
import './App.css'
import {
  fetchProfile,
  generateReadme,
  type GeneratedReadme,
  type ProfileData,
  type ReadmeConfig,
} from './api'

const IMAGE_PROXY_HOSTS = [
  'github-readme-stats.vercel.app',
  'github-readme-stats-fast.vercel.app',
  'streak-stats.demolab.com',
  'img.shields.io',
]

function imageSrcForPreview(src: string | undefined): string {
  if (!src) return ''
  try {
    const u = new URL(src, window.location.origin)
    if (IMAGE_PROXY_HOSTS.includes(u.hostname.toLowerCase())) {
      return `/api/proxy-image?url=${encodeURIComponent(src)}`
    }
  } catch {
    // URL inválida, devolver tal cual
  }
  return src
}

type SectionKey = 'header' | 'bio' | 'stats' | 'languages' | 'repos' | 'badges' | 'charts'

const sectionLabels: Record<SectionKey, string> = {
  header: 'Header',
  bio: 'About',
  stats: 'Stats',
  languages: 'Languages',
  repos: 'Repos',
  badges: 'Badges',
  charts: 'Charts',
}

const defaultSections: Record<SectionKey, boolean> = {
  header: true,
  bio: true,
  stats: true,
  languages: true,
  repos: true,
  badges: false,
  charts: false,
}

type TemplateId = 'minimal' | 'professional' | 'creative'

const TEMPLATE_OPTIONS: { value: TemplateId; label: string; sections: Record<SectionKey, boolean> }[] = [
  { value: 'minimal', label: 'Minimal (solo header, about, proyectos)', sections: { header: true, bio: true, stats: false, languages: false, repos: true, badges: false, charts: false } },
  { value: 'professional', label: 'Professional (completo, títulos formales)', sections: { header: true, bio: true, stats: true, languages: true, repos: true, badges: true, charts: true } },
  { value: 'creative', label: 'Creative (completo con emojis)', sections: { header: true, bio: true, stats: true, languages: true, repos: true, badges: true, charts: true } },
]

const LAYOUT_OPTIONS: { value: string; label: string }[] = [
  { value: 'default', label: 'Lista completa (con estrellas e idioma)' },
  { value: 'compact', label: 'Lista compacta (solo enlaces)' },
  { value: 'table', label: 'Tabla' },
]

const SECTION_ORDER: SectionKey[] = ['header', 'badges', 'bio', 'stats', 'languages', 'repos', 'charts']

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
  const [layout, setLayout] = useState('default')
  const [template, setTemplate] = useState<TemplateId>('professional')
  const [sections, setSections] = useState<Record<SectionKey, boolean>>(
    TEMPLATE_OPTIONS[1].sections,
  )
  const [copyStatus, setCopyStatus] = useState<string | null>(null)
  const [showSections, setShowSections] = useState(false)
  const [previewViewMode, setPreviewViewMode] = useState<'preview' | 'markdown'>('preview')

  const trimmedUsername = username.trim()

  const selectedSections = useMemo(
    () =>
      SECTION_ORDER.filter((key) => sections[key]),
    [sections],
  )

  const config: ReadmeConfig = useMemo(
    () => ({
      sections: selectedSections,
      theme,
      layout,
      template,
    }),
    [selectedSections, theme, layout, template],
  )

  const handleTemplateChange = (newTemplate: TemplateId) => {
    setTemplate(newTemplate)
    const option = TEMPLATE_OPTIONS.find((t) => t.value === newTemplate)
    if (option) setSections(option.sections)
  }

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
      const nextAssets = getAssets(result)
      if (typeof nextMarkdown !== 'string') {
        setGenerateError('Respuesta sin markdown.')
        setMarkdown('')
        setAssets(null)
        return
      }
      setMarkdown(nextMarkdown)
      setAssets(nextAssets && typeof nextAssets === 'object' ? nextAssets : null)
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
        <h1>GitHub Profile README</h1>
        <p className="app-subtitle">
          Genera el markdown para el README de tu perfil en tres pasos.
        </p>
      </header>

      <div className="layout">
        <div className="left-column">
          <section className="panel panel-main">
            <div className="hero">
              <label htmlFor="username" className="hero-label">Tu usuario de GitHub</label>
              <form className="hero-form" onSubmit={handleProfileSubmit}>
                <input
                  id="username"
                  type="text"
                  placeholder="ej. octocat"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="hero-input"
                />
                <button
                  type="submit"
                  className="button primary hero-btn"
                  disabled={!trimmedUsername || profileLoading}
                >
                  {profileLoading ? 'Cargando…' : 'Cargar perfil'}
                </button>
              </form>
            </div>
            {profileError && <p className="status error">{profileError}</p>}

            {profile && (
              <div className="profile-compact">
                <div className="profile-compact-main">
                  <strong>{profileName}</strong>
                  <span className="profile-compact-username">@{profile.username}</span>
                </div>
                <p className="profile-compact-bio">{profileBio}</p>
                <div className="profile-compact-stats">
                  <span>{formatNumber(profile.followers)} seguidores</span>
                  <span className="dot">·</span>
                  <span>{formatNumber(profile.public_repos)} repos</span>
                  {topLanguages.length > 0 && (
                    <>
                      <span className="dot">·</span>
                      <span>{topLanguages.slice(0, 3).map(([l]) => l).join(', ')}</span>
                    </>
                  )}
                </div>
              </div>
            )}

            <div className="options-row">
              <div className="option-group">
                <label htmlFor="template">Plantilla</label>
                <select
                  id="template"
                  value={template}
                  onChange={(e) => handleTemplateChange(e.target.value as TemplateId)}
                >
                  {TEMPLATE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
              <div className="option-group">
                <label htmlFor="theme">Tema</label>
                <select id="theme" value={theme} onChange={(e) => setTheme(e.target.value)}>
                  <option value="light">Claro</option>
                  <option value="dark">Oscuro</option>
                  <option value="auto">Auto</option>
                </select>
              </div>
              <div className="option-group">
                <label htmlFor="layout">Repos</label>
                <select id="layout" value={layout} onChange={(e) => setLayout(e.target.value)}>
                  {LAYOUT_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <button
              type="button"
              className="link-button"
              onClick={() => setShowSections(!showSections)}
              aria-expanded={showSections}
            >
              {showSections ? 'Ocultar secciones' : 'Personalizar secciones'}
            </button>
            {showSections && (
              <div className="sections-grid">
                {SECTION_ORDER.map((key) => (
                  <label className="checkbox" key={key}>
                    <input
                      type="checkbox"
                      checked={sections[key]}
                      onChange={() => toggleSection(key)}
                    />
                    <span>{sectionLabels[key]}</span>
                  </label>
                ))}
              </div>
            )}

            <div className="actions-main">
              <form onSubmit={(e) => { e.preventDefault(); handleGenerate() }} style={{ display: 'inline' }}>
                <button
                  type="submit"
                  className="button primary btn-generate"
                  disabled={!trimmedUsername || generateLoading}
                >
                  {generateLoading ? 'Generando…' : 'Generar README'}
                </button>
              </form>
              <button
                type="button"
                className="button secondary"
                onClick={() => { setMarkdown(''); setAssets(null); setGenerateError(null) }}
              >
                Limpiar
              </button>
            </div>
            {generateError && <p className="status error">{generateError}</p>}
          </section>
        </div>

        <section className="panel preview-panel">
          <div className="preview-header">
            <h2>Vista previa</h2>
            <div className="toolbar">
              <div className="preview-view-switch" role="tablist" aria-label="Vista">
                <button
                  type="button"
                  role="tab"
                  aria-selected={previewViewMode === 'preview'}
                  className={previewViewMode === 'preview' ? 'tab active' : 'tab'}
                  onClick={() => setPreviewViewMode('preview')}
                >
                  Vista previa
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={previewViewMode === 'markdown'}
                  className={previewViewMode === 'markdown' ? 'tab active' : 'tab'}
                  onClick={() => setPreviewViewMode('markdown')}
                >
                  Markdown
                </button>
              </div>
              <button
                type="button"
                className="button ghost"
                onClick={handleCopy}
                disabled={!markdown}
              >
                {copyStatus === 'Copiado.' ? '✓ Copiado' : 'Copiar'}
              </button>
              <button
                type="button"
                className="button ghost"
                onClick={handleDownload}
                disabled={!markdown}
              >
                Descargar
              </button>
            </div>
          </div>

          {previewViewMode === 'preview' && (
            <div className="preview-box">
              {markdown ? (
                <div className="markdown-body">
                  <ReactMarkdown
                    rehypePlugins={[rehypeRaw]}
                    components={{
                      img: ({ src, alt, ...props }) => (
                        <img
                          {...props}
                          src={imageSrcForPreview(src)}
                          alt={alt ?? ''}
                          referrerPolicy="no-referrer"
                          loading="lazy"
                        />
                      ),
                    }}
                  >
                    {markdown}
                  </ReactMarkdown>
                </div>
              ) : (
                <p className="status empty">
                  Carga tu usuario y pulsa «Generar README» para ver la vista previa.
                </p>
              )}
            </div>
          )}

          {previewViewMode === 'markdown' && (
            <div className="markdown-edit-box">
              <textarea
                id="markdown-edit"
                aria-label="Editar markdown"
                rows={18}
                value={markdown}
                onChange={(e) => setMarkdown(e.target.value)}
                className="field textarea-editable"
                placeholder="Genera el README para cargar el markdown aquí, o edítalo manualmente."
              />
              <button
                type="button"
                className="button primary btn-recompile"
                onClick={() => setPreviewViewMode('preview')}
              >
                Actualizar vista previa
              </button>
            </div>
          )}

          {assets && Object.keys(assets).length > 0 && (
            <details className="assets-details">
              <summary>Assets generados</summary>
              <ul className="asset-list">
                {Object.entries(assets).map(([name, url]) => (
                  <li key={name}>
                    <a href={url} target="_blank" rel="noreferrer">{name}</a>
                  </li>
                ))}
              </ul>
            </details>
          )}
        </section>
      </div>
    </div>
  )
}

export default App
