import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Container,
  Title,
  Text,
  Badge,
  Stack,
  Group,
  LoadingOverlay,
  Anchor,
  Breadcrumbs,
  Grid,
  Image,
  Card,
  Paper,
  Divider,
  Button,
  FileButton,
  Alert,
  Modal,
  TextInput,
  ActionIcon,
} from '@mantine/core'
import MDEditor from '@uiw/react-md-editor'
import ReactMarkdown from 'react-markdown'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { useAuth } from '../contexts/AuthContext'
import { toSlug } from '../utils/slug'

interface Game {
  title: string
  manufacturer: string
  console: string
  type?: string  // "trivial" or "hidden_gem"
}

interface GameDetails {
  title: string
  description: string
  images: string[]
  image_count: number
  tags?: string[]
}

interface GameImage {
  filename: string
  url: string
}

interface SortableImageProps {
  image: GameImage
  index: number
  onDelete: (filename: string) => void
  API_URL: string
  gameTitle: string
}

function SortableImage({ image, index, onDelete, API_URL, gameTitle }: SortableImageProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: image.filename })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <Grid.Col span={{ base: 12, sm: 6, md: 3 }} ref={setNodeRef} style={style}>
      <Card p="xs" withBorder>
        {index === 0 && (
          <Badge color="blue" variant="light" mb="xs" size="sm">
            Fedlap
          </Badge>
        )}
        <div {...attributes} {...listeners} style={{ cursor: 'grab' }}>
          <Image
            src={`${API_URL}${image.url}`}
            radius="md"
            alt={`${gameTitle} ${index + 1}`}
            fallbackSrc="https://via.placeholder.com/400x300"
          />
        </div>
        <Button
          color="red"
          variant="light"
          size="xs"
          fullWidth
          mt="xs"
          onClick={() => onDelete(image.filename)}
        >
          Törlés
        </Button>
      </Card>
    </Grid.Col>
  )
}

function GameDetail() {
  const { manufacturer, platform, slug } = useParams<{ manufacturer: string; platform: string; slug: string }>()
  const navigate = useNavigate()
  const { isAuthenticated, user, token } = useAuth()
  const [game, setGame] = useState<Game | null>(null)
  const [gameDetails, setGameDetails] = useState<GameDetails | null>(null)
  const [loading, setLoading] = useState(true)
  
  // Debug logging
  console.log('GameDetail render:', { manufacturer, platform, slug, loading, game: game?.title })
  const [editingDescription, setEditingDescription] = useState(false)
  const [descriptionText, setDescriptionText] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [adminImages, setAdminImages] = useState<GameImage[]>([])
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [imageToDelete, setImageToDelete] = useState<string | null>(null)
  const [reorderingImages, setReorderingImages] = useState(false)
  const [editingTags, setEditingTags] = useState(false)
  const [tagsText, setTagsText] = useState<string[]>([])
  const [newTagInput, setNewTagInput] = useState('')

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  const API_URL = 'http://localhost:8000'

  useEffect(() => {
    if (slug && manufacturer && platform) {
      // Find game by matching slug - we'll search and match
      fetchGameBySlug(slug, manufacturer, platform).catch((error) => {
        console.error('Error in fetchGameBySlug:', error)
        setError('Hiba a játék betöltésekor')
        setLoading(false)
      })
    } else if (!slug || !manufacturer || !platform) {
      // If any required param is missing, show error
      setError('Hiányzó URL paraméterek')
      setLoading(false)
    }
  }, [slug, manufacturer, platform])

  useEffect(() => {
    if (game && isAuthenticated && user?.is_admin && token) {
      loadAdminImages()
    }
  }, [game, isAuthenticated, user, token])

  const fetchGameBySlug = async (gameSlug: string, mfrSlug: string, pltSlug: string) => {
    console.log('fetchGameBySlug called:', { gameSlug, mfrSlug, pltSlug })
    try {
      setLoading(true)
      setError(null)
      
      // Get all manufacturers and find the one matching the slug
      const manufacturersResponse = await fetch(`${API_URL}/manufacturers`)
      const manufacturersData = await manufacturersResponse.json()
      
      const manufacturer = manufacturersData.manufacturers.find((mfr: any) => 
        toSlug(mfr.name) === mfrSlug
      )
      
      if (!manufacturer) {
        setError(`Gyártó nem található: ${mfrSlug}`)
        setLoading(false)
        return
      }
      
      // Find platform matching the slug
      const platform = manufacturer.platforms.find((plt: string) => 
        toSlug(plt) === pltSlug
      )
      
      if (!platform) {
        setError(`Platform nem található: ${pltSlug}`)
        setLoading(false)
        return
      }
      
      // Get games for this manufacturer and platform
      const response = await fetch(`${API_URL}/manufacturer/${encodeURIComponent(manufacturer.name)}/${encodeURIComponent(platform)}`)
      const data = await response.json()
      
      if (!data.games || data.games.length === 0) {
        setError(`Nincsenek játékok a ${manufacturer.name} ${platform} platformon`)
        setLoading(false)
        return
      }
      
      // Find game by matching slug
      const foundGame = data.games.find((g: Game) => 
        toSlug(g.title) === gameSlug
      )
      
      if (foundGame) {
        await fetchGame(foundGame.title, true)
      } else {
        setError(`Játék nem található: ${gameSlug}`)
        setLoading(false)
      }
    } catch (error) {
      console.error('Error fetching game by slug:', error)
      setError('Hiba a játék betöltésekor')
      setLoading(false)
    }
  }

  const fetchGame = async (gameTitle: string, skipLoadingState: boolean = false) => {
    try {
      if (!skipLoadingState) {
        setLoading(true)
      }
      setError(null)
      
      // Search for the game - try exact match first, then partial match
      const response = await fetch(`${API_URL}/games/search?q=${encodeURIComponent(gameTitle)}`)
      const data = await response.json()
      
      // Find exact match (case-insensitive)
      let foundGame = data.games.find((g: Game) => 
        g.title.toLowerCase() === gameTitle.toLowerCase()
      )
      
      // If no exact match, try to find the closest match
      if (!foundGame && data.games.length > 0) {
        // Try to find a game that contains the title
        foundGame = data.games.find((g: Game) => 
          g.title.toLowerCase().includes(gameTitle.toLowerCase()) ||
          gameTitle.toLowerCase().includes(g.title.toLowerCase())
        )
        // If still not found, use the first result
        if (!foundGame) {
          foundGame = data.games[0]
        }
      }
      
      if (foundGame) {
        setGame(foundGame)
        
        // Fetch game details (description + images)
        try {
          const detailsResponse = await fetch(
            `${API_URL}/games/${encodeURIComponent(foundGame.title)}/details?console=${encodeURIComponent(foundGame.console)}`
          )
          if (detailsResponse.ok) {
            const detailsData = await detailsResponse.json()
            setGameDetails(detailsData)
            setDescriptionText(detailsData.description || '')
            setTagsText(detailsData.tags || [])
          }
        } catch (error) {
          console.error('Error fetching game details:', error)
        }
      } else {
        setError(`Játék nem található: ${gameTitle}`)
      }
      setLoading(false)
    } catch (error) {
      console.error('Error fetching game:', error)
      setError('Hiba a játék betöltésekor')
      setLoading(false)
    }
  }

  const getColorForManufacturer = (mfrName: string): string => {
    const colors: { [key: string]: string } = {
      Nintendo: 'red',
      Sony: 'blue',
      Sega: 'teal',
      Microsoft: 'green',
      SNK: 'orange',
      NEC: 'purple',
      PC: 'grape',
      Commodore: 'cyan',
      Sinclair: 'yellow',
      'Pico-8': 'pink',
    }
    return colors[mfrName] || 'gray'
  }


  const generateTags = (title: string): string[] => {
    const allTags = ['Action', 'Adventure', 'RPG', 'Platformer', 'Puzzle', 'Strategy', 'Shooter', 'Racing', 'Simulation', 'Fighting', 'Hidden Gem', 'Cult Classic', 'Retro Gaming', 'Indie']
    const hash = title.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
    const numTags = 3 + (hash % 4)
    const selectedTags = []
    let currentHash = hash
    
    for (let i = 0; i < numTags; i++) {
      selectedTags.push(allTags[currentHash % allTags.length])
      currentHash = Math.floor(currentHash / allTags.length)
    }
    
    return [...new Set(selectedTags)]
  }

  const loadAdminImages = async () => {
    if (!game || !token) return
    
    try {
      const response = await fetch(
        `${API_URL}/admin/games/${encodeURIComponent(game.title)}/images`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )
      if (response.ok) {
        const data = await response.json()
        setAdminImages(data.images || [])
      }
    } catch (error) {
      console.error('Error loading admin images:', error)
    }
  }

  const saveDescription = async () => {
    if (!game || !token) return
    
    setSaving(true)
    setError(null)
    
    try {
      const response = await fetch(
        `${API_URL}/admin/games/${encodeURIComponent(game.title)}/description`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ description: descriptionText })
        }
      )

      if (!response.ok) {
        let errorMessage = `Hiba a leírás mentésekor: ${response.status}`
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorData.message || errorMessage
        } catch {
          // If response is not JSON, use status text
          errorMessage = `Hiba a leírás mentésekor: ${response.status} ${response.statusText}`
        }
        throw new Error(errorMessage)
      }

      setEditingDescription(false)
      // Reload game details
      if (game) {
        const detailsResponse = await fetch(
          `${API_URL}/games/${encodeURIComponent(game.title)}/details?console=${encodeURIComponent(game.console)}`
        )
        const detailsData = await detailsResponse.json()
        setGameDetails(detailsData)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Hiba a leírás mentésekor')
    } finally {
      setSaving(false)
    }
  }

  const deleteDescription = async () => {
    if (!game || !token) return
    
    if (!confirm('Biztosan törölni szeretnéd a leírást?')) return
    
    setSaving(true)
    setError(null)
    
    try {
      const response = await fetch(
        `${API_URL}/admin/games/${encodeURIComponent(game.title)}/description`,
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

      setDescriptionText('')
      setEditingDescription(false)
      // Reload game details
      if (game) {
        const detailsResponse = await fetch(
          `${API_URL}/games/${encodeURIComponent(game.title)}/details?console=${encodeURIComponent(game.console)}`
        )
        const detailsData = await detailsResponse.json()
        setGameDetails(detailsData)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Hiba a leírás törlésekor')
    } finally {
      setSaving(false)
    }
  }

  const uploadImage = async (file: File) => {
    if (!game || !token) return
    
    setSaving(true)
    setError(null)
    
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const response = await fetch(
        `${API_URL}/admin/games/${encodeURIComponent(game.title)}/images`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        }
      )

      if (!response.ok) {
        let errorMessage = `Hiba a kép feltöltésekor: ${response.status}`
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorData.message || errorMessage
        } catch {
          errorMessage = `Hiba a kép feltöltésekor: ${response.status} ${response.statusText}`
        }
        throw new Error(errorMessage)
      }

      // Reload images
      await loadAdminImages()
      // Reload game details
      if (game) {
        const detailsResponse = await fetch(
          `${API_URL}/games/${encodeURIComponent(game.title)}/details?console=${encodeURIComponent(game.console)}`
        )
        const detailsData = await detailsResponse.json()
        setGameDetails(detailsData)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Hiba a kép feltöltésekor')
    } finally {
      setSaving(false)
    }
  }

  const confirmDeleteImage = (filename: string) => {
    setImageToDelete(filename)
    setDeleteModalOpen(true)
  }

  const deleteImage = async () => {
    if (!game || !token || !imageToDelete) return
    
    setSaving(true)
    setError(null)
    
    try {
      const response = await fetch(
        `${API_URL}/admin/games/${encodeURIComponent(game.title)}/images/${encodeURIComponent(imageToDelete)}`,
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
      await loadAdminImages()
      // Reload game details
      if (game) {
        const detailsResponse = await fetch(
          `${API_URL}/games/${encodeURIComponent(game.title)}/details?console=${encodeURIComponent(game.console)}`
        )
        const detailsData = await detailsResponse.json()
        setGameDetails(detailsData)
      }
      setDeleteModalOpen(false)
      setImageToDelete(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Hiba a kép törlésekor')
    } finally {
      setSaving(false)
    }
  }

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event
    
    if (!over || active.id === over.id || !game || !token) {
      return
    }

    const oldIndex = adminImages.findIndex((img) => img.filename === active.id)
    const newIndex = adminImages.findIndex((img) => img.filename === over.id)

    if (oldIndex === -1 || newIndex === -1) {
      return
    }

    // Optimistically update the UI
    const newImages = arrayMove(adminImages, oldIndex, newIndex)
    setAdminImages(newImages)
    setReorderingImages(true)

    try {
      // Update order on backend
      const response = await fetch(
        `${API_URL}/admin/games/${encodeURIComponent(game.title)}/images/order`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            order: newImages.map((img) => img.filename)
          })
        }
      )

      if (!response.ok) {
        let errorMessage = `Hiba a képek sorrendjének mentésekor: ${response.status}`
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorData.message || errorMessage
        } catch {
          errorMessage = `Hiba a képek sorrendjének mentésekor: ${response.status} ${response.statusText}`
        }
        throw new Error(errorMessage)
      }

      // Reload admin images to reflect new order
      await loadAdminImages()
      
      // Reload game details to reflect new order
      if (game) {
        const detailsResponse = await fetch(
          `${API_URL}/games/${encodeURIComponent(game.title)}/details?console=${encodeURIComponent(game.console)}`
        )
        const detailsData = await detailsResponse.json()
        setGameDetails(detailsData)
      }
    } catch (err) {
      // Revert on error - reload original images
      await loadAdminImages()
      setError(err instanceof Error ? err.message : 'Hiba a képek sorrendjének mentésekor')
    } finally {
      setReorderingImages(false)
    }
  }

  const saveTags = async () => {
    if (!game || !token) return
    
    setSaving(true)
    setError(null)
    
    try {
      const response = await fetch(
        `${API_URL}/admin/games/${encodeURIComponent(game.title)}/tags`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ tags: tagsText })
        }
      )

      if (!response.ok) {
        let errorMessage = `Hiba a címkék mentésekor: ${response.status}`
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorData.message || errorMessage
        } catch {
          errorMessage = `Hiba a címkék mentésekor: ${response.status} ${response.statusText}`
        }
        throw new Error(errorMessage)
      }

      setEditingTags(false)
      // Reload game details
      if (game) {
        const detailsResponse = await fetch(
          `${API_URL}/games/${encodeURIComponent(game.title)}/details?console=${encodeURIComponent(game.console)}`
        )
        const detailsData = await detailsResponse.json()
        setGameDetails(detailsData)
        setTagsText(detailsData.tags || [])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Hiba a címkék mentésekor')
    } finally {
      setSaving(false)
    }
  }

  const deleteTags = async () => {
    if (!game || !token) return
    
    setSaving(true)
    setError(null)
    
    try {
      const response = await fetch(
        `${API_URL}/admin/games/${encodeURIComponent(game.title)}/tags`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (!response.ok) {
        throw new Error('Hiba a címkék törlésekor')
      }

      setTagsText([])
      setEditingTags(false)
      // Reload game details
      if (game) {
        const detailsResponse = await fetch(
          `${API_URL}/games/${encodeURIComponent(game.title)}/details?console=${encodeURIComponent(game.console)}`
        )
        const detailsData = await detailsResponse.json()
        setGameDetails(detailsData)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Hiba a címkék törlésekor')
    } finally {
      setSaving(false)
    }
  }

  const addTag = () => {
    if (newTagInput.trim() && !tagsText.includes(newTagInput.trim())) {
      setTagsText([...tagsText, newTagInput.trim()])
      setNewTagInput('')
    }
  }

  const removeTag = (tagToRemove: string) => {
    setTagsText(tagsText.filter(tag => tag !== tagToRemove))
  }

  if (loading) {
    return (
      <Container>
        <LoadingOverlay visible={loading} />
      </Container>
    )
  }

  if (!game && !loading) {
    return (
      <Container>
        <Title order={2}>Játék nem található</Title>
        {error && (
          <Alert color="red" mt="md" title="Hiba">
            {error}
          </Alert>
        )}
        {slug && manufacturer && platform && (
          <Text mt="md" c="dimmed">
            Keresett játék: {slug} ({manufacturer} - {platform})
          </Text>
        )}
      </Container>
    )
  }

  const items = [
    { title: 'Gyártók', href: '/manufacturers' },
    { title: game.manufacturer, href: `/manufacturer/${toSlug(game.manufacturer)}` },
    { title: game.console, href: `/manufacturer/${toSlug(game.manufacturer)}/${toSlug(game.console)}` },
    { title: game.title, href: '#' },
  ].map((item, index) => (
    <Anchor key={index} onClick={() => navigate(item.href)}>
      {item.title}
    </Anchor>
  ))

  // Use stored tags if available, otherwise generate from title
  const tags = gameDetails?.tags && gameDetails.tags.length > 0 
    ? gameDetails.tags 
    : generateTags(game.title)
  const description = gameDetails?.description || `${game.title} egy játék a ${game.console} platformon.`
  // Use adminImages if available and user is admin, otherwise use gameDetails images
  const displayImages = isAuthenticated && user?.is_admin && adminImages.length > 0
    ? adminImages.map(img => img.url)
    : (gameDetails?.images || [])
  
  const mainImage = displayImages.length > 0 
    ? `${API_URL}${displayImages[0]}` 
    : `https://via.placeholder.com/800x600?text=${encodeURIComponent(game.title)}`
  const galleryImages = displayImages
  
  // Debug: log admin state
  console.log('GameDetail admin state:', { 
    isAuthenticated, 
    isAdmin: user?.is_admin, 
    adminImagesCount: adminImages.length,
    galleryImagesCount: galleryImages.length 
  })

  return (
    <Container>
      <Breadcrumbs mb="lg">{items}</Breadcrumbs>

      <Grid gutter="xl">
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card shadow="md" padding="lg" radius="md" withBorder>
            <Image
              src={mainImage}
              radius="md"
              alt={game.title}
              fallbackSrc="https://via.placeholder.com/800x600"
            />
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 8 }}>
          <Stack gap="md">
            <div>
              <Title order={1} mb="xs">{game.title}</Title>
              <Group gap="xs">
                <Badge variant="light" color={getColorForManufacturer(game.manufacturer)} size="lg">
                  {game.manufacturer}
                </Badge>
                <Badge variant="light" color="blue" size="lg">
                  {game.console}
                </Badge>
                {game.type === "trivial" ? (
                  <Badge variant="filled" color="blue" size="lg">
                    Triviális
                  </Badge>
                ) : (
                  <Badge variant="filled" color="violet" size="lg">
                    Hidden Gem
                  </Badge>
                )}
              </Group>
            </div>

            <Divider />

            <div>
              <Group justify="space-between" mb="sm">
                <Title order={3}>Leírás</Title>
                {isAuthenticated && user?.is_admin && (
                  <Group gap="xs">
                    {!editingDescription ? (
                      <Button size="xs" variant="light" onClick={() => setEditingDescription(true)}>
                        Szerkesztés
                      </Button>
                    ) : (
                      <>
                        <Button size="xs" onClick={saveDescription} loading={saving}>
                          Mentés
                        </Button>
                        <Button size="xs" variant="light" onClick={() => {
                          setEditingDescription(false)
                          setDescriptionText(description)
                        }}>
                          Mégse
                        </Button>
                        <Button size="xs" variant="light" color="red" onClick={deleteDescription} loading={saving}>
                          Törlés
                        </Button>
                      </>
                    )}
                  </Group>
                )}
              </Group>
              {error && (
                <Alert color="red" mb="sm" title="Hiba">
                  {error}
                </Alert>
              )}
              {editingDescription && isAuthenticated && user?.is_admin ? (
                <div data-color-mode="light">
                  <MDEditor
                    value={descriptionText}
                    onChange={(value) => setDescriptionText(value || '')}
                    preview="edit"
                    hideToolbar={false}
                    visibleDragBar={false}
                    height={400}
                  />
                  <Text size="xs" c="dimmed" mt="xs">
                    Tipp: Használd a **bold**, *italic*, [link](url) markdown formázást
                  </Text>
                </div>
              ) : (
                <div data-color-mode="light">
                  <ReactMarkdown
                    components={{
                      p: ({ children }) => <Text style={{ marginBottom: '1em', lineHeight: 1.7 }}>{children}</Text>,
                      strong: ({ children }) => <strong style={{ fontWeight: 600 }}>{children}</strong>,
                      em: ({ children }) => <em style={{ fontStyle: 'italic' }}>{children}</em>,
                      a: ({ href, children }) => <Anchor href={href} target="_blank" rel="noopener noreferrer">{children}</Anchor>,
                    }}
                  >
                    {description}
                  </ReactMarkdown>
                </div>
              )}
            </div>

            <div>
              <Group justify="space-between" mb="sm">
                <Title order={3}>Műfaj</Title>
                {isAuthenticated && user?.is_admin && (
                  <Group gap="xs">
                    {!editingTags ? (
                      <>
                        <Button size="xs" variant="light" onClick={() => {
                          setEditingTags(true)
                          setTagsText(tags)
                        }}>
                          Szerkesztés
                        </Button>
                        {tags.length > 0 && (
                          <Button size="xs" color="red" variant="light" onClick={deleteTags} loading={saving}>
                            Törlés
                          </Button>
                        )}
                      </>
                    ) : (
                      <>
                        <Button size="xs" onClick={saveTags} loading={saving}>
                          Mentés
                        </Button>
                        <Button size="xs" variant="light" onClick={() => {
                          setEditingTags(false)
                          setTagsText(tags)
                          setNewTagInput('')
                        }}>
                          Mégse
                        </Button>
                      </>
                    )}
                  </Group>
                )}
              </Group>
              {editingTags && isAuthenticated && user?.is_admin ? (
                <Stack gap="xs">
                  <Group gap="xs" wrap="wrap">
                    {tagsText.map((tag, idx) => (
                      <Badge key={idx} variant="outline" size="sm">
                        {tag}
                        <ActionIcon
                          size="xs"
                          color="red"
                          variant="transparent"
                          onClick={() => removeTag(tag)}
                          style={{ marginLeft: 4 }}
                        >
                          ×
                        </ActionIcon>
                      </Badge>
                    ))}
                  </Group>
                  <Group gap="xs">
                    <TextInput
                      placeholder="Új címke"
                      value={newTagInput}
                      onChange={(e) => setNewTagInput(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault()
                          addTag()
                        }
                      }}
                      size="xs"
                      style={{ flex: 1 }}
                    />
                    <Button size="xs" onClick={addTag}>
                      Hozzáadás
                    </Button>
                  </Group>
                </Stack>
              ) : (
                <Group gap="xs">
                  {tags.map((tag, idx) => (
                    <Badge key={idx} variant="outline" size="sm">
                      {tag}
                    </Badge>
                  ))}
                </Group>
              )}
            </div>

            <Group mt="lg">
              <Button
                variant="light"
                onClick={() => navigate(`/manufacturer/${toSlug(game.manufacturer)}/${toSlug(game.console)}`)}
              >
                ← Vissza a platform listához
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate(`/manufacturer/${toSlug(game.manufacturer)}`)}
              >
                Több játék {game.manufacturer}-tól
              </Button>
            </Group>
          </Stack>
        </Grid.Col>

        {(galleryImages.length > 0 || (isAuthenticated && user?.is_admin)) && (
          <Grid.Col span={12}>
            <Paper shadow="sm" p="md" radius="md" withBorder>
              <Group justify="space-between" mb="sm">
                <Title order={3}>Képek</Title>
                {isAuthenticated && user?.is_admin ? (
                  <FileButton
                    onChange={uploadImage}
                    accept="image/*"
                  >
                    {(props) => (
                      <Button {...props} size="xs" loading={saving}>
                        Kép feltöltése
                      </Button>
                    )}
                  </FileButton>
                ) : null}
              </Group>
              {galleryImages.length > 0 || (isAuthenticated && user?.is_admin && adminImages.length > 0) ? (
                isAuthenticated && user?.is_admin && adminImages.length > 0 ? (
                  <DndContext
                    sensors={sensors}
                    collisionDetection={closestCenter}
                    onDragEnd={handleDragEnd}
                  >
                    <SortableContext
                      items={adminImages.map(img => img.filename)}
                    >
                      <Grid gutter="md">
                        {adminImages.map((image, idx) => (
                          <SortableImage
                            key={image.filename}
                            image={image}
                            index={idx}
                            onDelete={confirmDeleteImage}
                            API_URL={API_URL}
                            gameTitle={game?.title || ''}
                          />
                        ))}
                      </Grid>
                    </SortableContext>
                  </DndContext>
                ) : (
                  <Grid gutter="md">
                    {galleryImages.map((imgPath, idx) => (
                      <Grid.Col key={idx} span={{ base: 12, sm: 6, md: 3 }}>
                        <Card p="xs" withBorder>
                          {idx === 0 && (
                            <Badge color="blue" variant="light" mb="xs" size="sm">
                              Fedlap
                            </Badge>
                          )}
                          <Image
                            src={`${API_URL}${imgPath}`}
                            radius="md"
                            alt={`${game.title} ${idx + 1}`}
                            fallbackSrc="https://via.placeholder.com/400x300"
                          />
                        </Card>
                      </Grid.Col>
                    ))}
                  </Grid>
                )
              ) : (
                <Text c="dimmed">Nincsenek képek</Text>
              )}
              {isAuthenticated && user?.is_admin && adminImages.length > 0 && (
                <Text size="xs" c="dimmed" mt="sm">
                  💡 Húzd át a képeket a sorrend változtatásához. Az első kép lesz a fedlap.
                </Text>
              )}
            </Paper>
          </Grid.Col>
        )}

        <Modal
          opened={deleteModalOpen}
          onClose={() => {
            setDeleteModalOpen(false)
            setImageToDelete(null)
          }}
          title="Kép törlése"
        >
          <Text>Biztosan törölni szeretnéd ezt a képet?</Text>
          <Group mt="md" justify="flex-end">
            <Button variant="light" onClick={() => {
              setDeleteModalOpen(false)
              setImageToDelete(null)
            }}>
              Mégse
            </Button>
            <Button color="red" onClick={deleteImage} loading={saving}>
              Törlés
            </Button>
          </Group>
        </Modal>
      </Grid>
    </Container>
  )
}

export default GameDetail


