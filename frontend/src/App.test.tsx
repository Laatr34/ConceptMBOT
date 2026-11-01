import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it } from 'vitest'
import App from './App'
import i18n from './i18n'

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

describe('App shell', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
  })

  it('renders the 14 navigation links', () => {
    renderAt('/')
    expect(screen.getByRole('navigation', { name: 'Main' }).querySelectorAll('a')).toHaveLength(14)
  })

  it('opens the in-app documentation page', () => {\n    renderAt('/documentation')\n    expect(screen.getByRole('heading', { name: 'RobotLab Web documentation' })).toBeInTheDocument()\n    expect(screen.getByRole('heading', { name: '1. What is RobotLab Web?' })).toBeInTheDocument()\n  })\n\n  it('labels unimplemented modules explicitly (no fake features)', () => {
    renderAt('/electrical')
    expect(screen.getByRole('status')).toHaveTextContent('Not implemented yet')
  })

  it('switches the component library to French', async () => {
    renderAt('/library')
    await userEvent.selectOptions(screen.getByLabelText('Language'), 'fr')
    expect(await screen.findByRole('heading', { name: 'Bibliothèque de composants' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Ajouter le composant' })).toBeInTheDocument()
  })
})
