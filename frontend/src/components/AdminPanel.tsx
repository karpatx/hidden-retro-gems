import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useNavigate } from 'react-router-dom'
import {
  Container,
  Title,
  Text,
  Button,
  TextInput,
  Stack,
  Paper,
  Group,
  Alert,
  Loader,
  Grid,
  Card,
  Image,
  FileButton
} from '@mantine/core'
// Using Mantine icons - if @tabler/icons-react is not available, we can use text buttons

const API_URL = 'http://localhost:8000'

interface Game {
  title: string
  manufacturer: string
  console: string
  type: string
}

interface GameImage {
  filename: string
  url: string
}

function AdminPanel() {
  const { isAuthenticated, user, token } = useAuth()
  const navigate = useNavigate()
  const [games, setGames] = useState<Game[]>([])
  const [selectedGame, setSelectedGame] = useState<Game | null>(null)
  const [description, setDescription] = useState('')
  const [images, setImages] = useState<GameImage[]>([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    if (!isAuthenticated || !user?.is_admin) {
      navigate('/login')
      return
    }
    loadGames()
  }, [isAuthenticated, user, navigate])

  const loadGames = async () => {
    try {
      const response = await fetch(`${API_URL}/games`)
      const data = await response.json()
      setGames(data.games || [])
    } catch (err) {
      setError('Hiba a játékok betöltésekor')
    }
  }

  const loadGameDetails = async (game: Game) => {
    setLoading(true)
    setError(null)
    setSelectedGame(game)
    
    try {
      // Load description
      const detailsResponse = await fetch(
        `${API_URL}/games/${encodeURIComponent(game.title)}/details`
      )
      if (detailsResponse.ok) {
        const details = await detailsResponse.json()
        setDescription(details.description || '')
      }

      // Load images
      const imagesResponse = await fetch(
        `${API_URL}/admin/games/${encodeURIComponent(game.title)}/images`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )
      if (imagesResponse.ok) {
        const imagesData = await imagesResponse.json()
        setImages(imagesData.images || [])
      }
    } catch (err) {
      setError('Hiba a játék adatok betöltésekor')
    } finally {
      setLoading(false)
    }
  }

  const saveDescription = async () => {
    if (!selectedGame) return
    
    setSaving(true)
    setError(null)
    
    try {
      const response = await fetch(
        `${API_URL}/admin/games/${encodeURIComponent(selectedGame.title)}/description`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ description })
        }
      )

      if (!response.ok) {
        throw new Error('Hiba a leírás mentésekor')
      }

      alert('Leírás sikeresen mentve!')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Hiba a leírás mentésekor')
    } finally {
      setSaving(false)
    }
  }

  const deleteDescription = async () => {
    if (!selectedGame) return
    
    if (!confirm('Biztosan törölni szeretnéd a leírást?')) return
    
    setSaving(true)
    setError(null)
    
    try {
      const response = await fetch(
        `${API_URL}/admin/games/${encodeURIComponent(selectedGame.title)}/description`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (!response.ok) {
        throw new Error('Hiba a leírás törlésekor')
      }

      setDescription('')
      alert('Leírás sikeresen törölve!')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Hiba a leírás törlésekor')
    } finally {
      setSaving(false)
    }
  }

  const uploadImage = async (file: File) => {
    if (!selectedGame) return
    
    setSaving(true)
    setError(null)
    
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const response = await fetch(
        `${API_URL}/admin/games/${encodeURIComponent(selectedGame.title)}/images`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        }
      )

      if (!response.ok) {
        throw new Error('Hiba a kép feltöltésekor')
      }

      // Reload images
      await loadGameDetails(selectedGame)
      alert('Kép sikeresen feltöltve!')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Hiba a kép feltöltésekor')
    } finally {
      setSaving(false)
    }
  }

  const deleteImage = async (filename: string) => {
    if (!selectedGame) return
    
    if (!confirm('Biztosan törölni szeretnéd ezt a képet?')) return
    
    setSaving(true)
    setError(null)
    
    try {
      const response = await fetch(
        `${API_URL}/admin/games/${encodeURIComponent(selectedGame.title)}/images/${encodeURIComponent(filename)}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (!response.ok) {
        throw new Error('Hiba a kép törlésekor')
      }

      // Reload images
      await loadGameDetails(selectedGame)
      alert('Kép sikeresen törölve!')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Hiba a kép törlésekor')
    } finally {
      setSaving(false)
    }
  }

  const filteredGames = games.filter(game =>
    game.title.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <Container size="xl" py="xl">
      <Title order={1} mb="xl">Admin Panel</Title>

      <Grid>
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Paper p="md" withBorder>
            <Stack gap="md">
              <TextInput
                placeholder="Keresés játékok között..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              
              <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
                <Stack gap="xs">
                  {filteredGames.map((game) => (
                    <Card
                      key={`${game.title}-${game.console}`}
                      p="sm"
                      style={{ cursor: 'pointer' }}
                      onClick={() => loadGameDetails(game)}
                      bg={selectedGame?.title === game.title ? 'blue.0' : undefined}
                    >
                      <Text size="sm" fw={500}>{game.title}</Text>
                      <Text size="xs" c="dimmed">
                        {game.manufacturer} - {game.console}
                      </Text>
                    </Card>
                  ))}
                </Stack>
              </div>
            </Stack>
          </Paper>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 8 }}>
          {selectedGame ? (
            <Paper p="md" withBorder>
              <Stack gap="md">
                <Title order={2}>{selectedGame.title}</Title>
                <Text c="dimmed">
                  {selectedGame.manufacturer} - {selectedGame.console}
                </Text>

                {error && (
                  <Alert color="red" title="Hiba">
                    {error}
                  </Alert>
                )}

                {loading ? (
                  <Loader />
                ) : (
                  <>
                    <div>
                      <Title order={4} mb="sm">Leírás</Title>
                      <textarea
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        style={{
                          width: '100%',
                          minHeight: '200px',
                          padding: '8px',
                          border: '1px solid #ced4da',
                          borderRadius: '4px',
                          fontFamily: 'inherit',
                          fontSize: '14px'
                        }}
                        placeholder="Játék leírása..."
                      />
                      <Group mt="sm">
                        <Button
                          onClick={saveDescription}
                          loading={saving}
                        >
                          Mentés
                        </Button>
                        <Button
                          variant="light"
                          color="red"
                          onClick={deleteDescription}
                          loading={saving}
                        >
                          Törlés
                        </Button>
                      </Group>
                    </div>

                    <div>
                      <Group justify="space-between" mb="sm">
                        <Title order={4}>Képek</Title>
                        <FileButton
                          onChange={uploadImage}
                          accept="image/*"
                        >
                          {(props) => (
                            <Button
                              {...props}
                              loading={saving}
                            >
                              Kép feltöltése
                            </Button>
                          )}
                        </FileButton>
                      </Group>

                      {images.length > 0 ? (
                        <Grid>
                          {images.map((img) => (
                            <Grid.Col key={img.filename} span={{ base: 12, sm: 6, md: 4 }}>
                              <Card p="sm" withBorder>
                                <Image
                                  src={`${API_URL}${img.url}`}
                                  alt={img.filename}
                                  height={200}
                                  fit="cover"
                                />
                                <Group justify="space-between" mt="sm">
                                  <Text size="xs" c="dimmed" truncate>
                                    {img.filename}
                                  </Text>
                                  <Button
                                    size="xs"
                                    color="red"
                                    variant="light"
                                    onClick={() => deleteImage(img.filename)}
                                    loading={saving}
                                  >
                                    Törlés
                                  </Button>
                                </Group>
                              </Card>
                            </Grid.Col>
                          ))}
                        </Grid>
                      ) : (
                        <Text c="dimmed">Nincsenek képek</Text>
                      )}
                    </div>
                  </>
                )}
              </Stack>
            </Paper>
          ) : (
            <Paper p="md" withBorder>
              <Text c="dimmed">Válassz ki egy játékot a szerkesztéshez</Text>
            </Paper>
          )}
        </Grid.Col>
      </Grid>
    </Container>
  )
}

export default AdminPanel

