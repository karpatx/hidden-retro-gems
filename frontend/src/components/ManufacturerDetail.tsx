import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import {
  Container,
  Title,
  Grid,
  Card,
  Text,
  Badge,
  Stack,
  Group,
  LoadingOverlay,
  Anchor,
  Breadcrumbs,
} from '@mantine/core'
import { useNavigate } from 'react-router-dom'

interface PlatformData {
  name: string
  games: Array<{
    title: string
    manufacturer: string
    console: string
  }>
}

function ManufacturerDetail() {
  const { name } = useParams<{ name: string }>()
  const navigate = useNavigate()
  const [data, setData] = useState<{
    name: string
    platforms: string[]
    total_games: number
    games: Array<{
      title: string
      manufacturer: string
      console: string
    }>
  } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (name) {
      fetchManufacturerDetail(name)
    }
  }, [name])

  const fetchManufacturerDetail = async (mfrName: string) => {
    try {
      const response = await fetch(`http://localhost:8000/manufacturer/${mfrName}`)
      const data = await response.json()
      setData(data)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching manufacturer detail:', error)
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

  if (loading) {
    return (
      <Container>
        <LoadingOverlay visible={loading} />
      </Container>
    )
  }

  if (!data) {
    return (
      <Container>
        <Title order={2}>Gyártó nem található</Title>
      </Container>
    )
  }

  // Group games by platform
  const platformsMap: { [key: string]: any[] } = {}
  data.games.forEach((game) => {
    if (!platformsMap[game.console]) {
      platformsMap[game.console] = []
    }
    platformsMap[game.console].push(game)
  })

  const platforms: PlatformData[] = Object.entries(platformsMap).map(
    ([platformName, games]) => ({
      name: platformName,
      games,
    })
  )

  const items = [
    { title: 'Gyártók', href: '/manufacturers' },
    { title: data.name, href: '#' },
  ].map((item, index) => (
    <Anchor key={index} onClick={() => navigate(item.href)}>
      {item.title}
    </Anchor>
  ))

  return (
    <Container>
      <Breadcrumbs mb="lg">{items}</Breadcrumbs>

      <Group justify="space-between" mb="lg">
        <Title order={1}>{data.name}</Title>
        <Badge variant="light" color={getColorForManufacturer(data.name)} size="lg">
          {data.total_games} játék
        </Badge>
      </Group>

      <Grid gutter="md">
        {platforms.map((platform) => (
          <Grid.Col key={platform.name} span={{ base: 12, md: 6, lg: 4 }}>
            <Anchor
              onClick={() => navigate(`/manufacturer/${data.name}/${platform.name}`)}
              underline="never"
            >
              <Card 
                shadow="sm" 
                padding="lg" 
                radius="md" 
                withBorder 
                style={{ height: '100%', cursor: 'pointer' }}
              >
                <Stack gap="xs">
                  <Group justify="space-between">
                    <Text fw={700} size="lg">
                      {platform.name}
                    </Text>
                    <Badge
                      variant="light"
                      color={getColorForManufacturer(data.name)}
                    >
                      {platform.games.length} játék
                    </Badge>
                  </Group>

                  <Group gap={4} mt="xs">
                    {platform.games.slice(0, 5).map((game, idx) => (
                      <Badge key={idx} variant="outline" size="xs" color="gray">
                        {game.title}
                      </Badge>
                    ))}
                    {platform.games.length > 5 && (
                      <Badge variant="dot" size="xs" color="gray">
                        +{platform.games.length - 5}
                      </Badge>
                    )}
                  </Group>
                </Stack>
              </Card>
            </Anchor>
          </Grid.Col>
        ))}
      </Grid>
    </Container>
  )
}

export default ManufacturerDetail

