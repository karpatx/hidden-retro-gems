import { Routes, Route, useNavigate } from 'react-router-dom'
import { AppShell, Burger, Group, Title, Container, Anchor, Button, Text } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { useAuth } from './contexts/AuthContext'
import Home from './components/Home'
import Games from './components/Games'
import About from './components/About'
import Manufacturers from './components/Manufacturers'
import ManufacturerDetail from './components/ManufacturerDetail'
import ManufacturerPlatformGames from './components/ManufacturerPlatformGames'
import GameDetail from './components/GameDetail'
import Login from './components/Login'

function App() {
  const [opened, { toggle }] = useDisclosure()
  const { isAuthenticated, user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{
        width: 200,
        breakpoint: 'sm',
        collapsed: { mobile: !opened, desktop: false },
      }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group>
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            <Title order={2}>Hidden Gem</Title>
          </Group>
          <Group>
            {isAuthenticated ? (
              <>
                <Text size="sm" c="dimmed">
                  {user?.email}
                  {user?.is_admin && ' (Admin)'}
                </Text>
                <Button variant="light" size="xs" onClick={handleLogout}>
                  Kijelentkezés
                </Button>
              </>
            ) : (
              <Button variant="light" size="xs" onClick={() => navigate('/login')}>
                Bejelentkezés
              </Button>
            )}
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md">
        <Group gap="xs">
          <Anchor href="/" underline="never" c="inherit">
            Főoldal
          </Anchor>
          <Anchor href="/manufacturers" underline="never" c="inherit">
            Gyártók
          </Anchor>
          <Anchor href="/games" underline="never" c="inherit">
            Játékok
          </Anchor>
          <Anchor href="/about" underline="never" c="inherit">
            Rólunk
          </Anchor>
        </Group>
      </AppShell.Navbar>

      <AppShell.Main>
        <Container size="xl">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/manufacturers" element={<Manufacturers />} />
            <Route path="/manufacturer/:name" element={<ManufacturerDetail />} />
            <Route path="/manufacturer/:name/:platform" element={<ManufacturerPlatformGames />} />
            <Route path="/manufacturer/:manufacturer/:platform/game/:slug" element={<GameDetail />} />
            <Route path="/games" element={<Games />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </Container>
      </AppShell.Main>
    </AppShell>
  )
}

export default App

