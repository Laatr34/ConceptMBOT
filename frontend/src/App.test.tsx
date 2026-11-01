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

  it('opens the in-app documentation page', () => {
    renderAt('/documentation')
    expect(screen.getByRole('heading', { name: 'RobotLab Web documentation' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '1. What is RobotLab Web?' })).toBeInTheDocument()
  })

  it('opens the electrical analysis module', () => {
    renderAt('/electrical')
    expect(screen.getByRole('heading', { name: 'Electrical Design' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Analyze electrical design' })).toBeInTheDocument()
  })

  it('opens the battery and autonomy module', () => {
    renderAt('/power')
    expect(screen.getByRole('heading', { name: 'Power & Battery' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Analyze battery' })).toBeInTheDocument()
  })

  it('labels unimplemented modules explicitly (no fake features)', () => {
    renderAt('/sensors')
    expect(screen.getByRole('status')).toHaveTextContent('Not implemented yet')
  })

  it('switches the component library to French', async () => {
    renderAt('/library')
    await userEvent.selectOptions(screen.getByLabelText('Language'), 'fr')
    expect(await screen.findByRole('heading', { name: 'Bibliothèque de composants' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Ajouter le composant' })).toBeInTheDocument()
  })
})
