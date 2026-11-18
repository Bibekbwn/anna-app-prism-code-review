'use client'

import { useRef, useState, type KeyboardEvent } from 'react'
import { MoreVertical } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { pages, type PageId } from './data'

type PrismHeaderProps = {
  activePage: PageId
  onNavigate: (page: PageId) => void
}

export function PrismHeader({ activePage, onNavigate }: PrismHeaderProps) {
  const [menuOpen, setMenuOpen] = useState(false)
  const menuButtonRef = useRef<HTMLButtonElement>(null)
  const pageLabel = pages.find((page) => page.id === activePage)?.label ?? 'New Review'

  function navigate(page: PageId) {
    setMenuOpen(false)
    onNavigate(page)
  }

  function closeMenuOnEscape(event: KeyboardEvent<HTMLElement>) {
    if (event.key !== 'Escape') return
    setMenuOpen(false)
    menuButtonRef.current?.focus()
  }

  return (
    <header className="topbar">
      <button className="brand" type="button" onClick={() => navigate('new')} aria-label="PRISM home">
        <span className="brand-mark" aria-hidden="true"><PrismLogo /></span>
        <span className="brand-copy">
          <strong>PRISM</strong>
          <small>Code Review Assistant</small>
        </span>
      </button>
      <span className="page-chip">{pageLabel}</span>
      <div className="navigation-wrap" onKeyDown={closeMenuOnEscape}>
        <Button
          ref={menuButtonRef}
          variant="outline"
          size="icon"
          aria-label="Open page navigation"
          aria-expanded={menuOpen}
          aria-controls="page-navigation"
          onClick={() => setMenuOpen((open) => !open)}
        >
          <MoreVertical aria-hidden="true" />
        </Button>
        {menuOpen && (
          <nav className="navigation-menu" id="page-navigation" aria-label="Page navigation">
            <span className="menu-label">Go to page</span>
            {pages.map((page, index) => (
              <button
                key={page.id}
                type="button"
                className={activePage === page.id ? 'menu-item active' : 'menu-item'}
                onClick={() => navigate(page.id)}
                aria-current={activePage === page.id ? 'page' : undefined}
              >
                <span>{String(index + 1).padStart(2, '0')}</span>
                {page.label}
              </button>
            ))}
            <div className="menu-footer"><span>Workspace</span><b>Local</b></div>
          </nav>
        )}
      </div>
    </header>
  )
}

function PrismLogo() {
  return (
    <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M16 3 28 25H4L16 3Z" />
      <path d="M16 3v13m0 0L4 25m12-9 12 9" />
    </svg>
  )
}
