import { NextRequest, NextResponse } from 'next/server'

const NOTION_TOKEN = process.env.NOTION_TOKEN
const NOTION_DB_ID = process.env.NOTION_DB_ID

export async function POST(req: NextRequest) {
  try {
    const { name, email } = await req.json()

    // Validation
    if (!name || !email) {
      return NextResponse.json(
        { error: '이름과 이메일을 모두 입력해주세요.' },
        { status: 400 }
      )
    }

    if (!NOTION_TOKEN || !NOTION_DB_ID) {
      console.error('Notion credentials not configured')
      return NextResponse.json(
        { error: '서버 설정 오류입니다. 관리자에게 문의하세요.' },
        { status: 500 }
      )
    }

    // Create Notion page
    // Convert to UUID format if needed (insert hyphens at positions 8, 12, 16, 20)
    const formattedDbId = NOTION_DB_ID!.length === 32 && !NOTION_DB_ID!.includes('-')
      ? `${NOTION_DB_ID!.slice(0, 8)}-${NOTION_DB_ID!.slice(8, 12)}-${NOTION_DB_ID!.slice(12, 16)}-${NOTION_DB_ID!.slice(16, 20)}-${NOTION_DB_ID!.slice(20)}`
      : NOTION_DB_ID!

    const notionPayload = {
      parent: {
        database_id: formattedDbId,
      },
      properties: {
        '이름': {
          title: [
            {
              text: {
                content: name,
              },
            },
          ],
        },
        '이메일': {
          email: email,
        },
        '신청일시': {
          date: {
            start: new Date().toISOString(),
          },
        },
      },
    }

    const response = await fetch('https://api.notion.com/v1/pages', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${NOTION_TOKEN}`,
        'Content-Type': 'application/json',
        'Notion-Version': '2022-06-28',
      },
      body: JSON.stringify(notionPayload),
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error('[Notion API] Error response:', {
        status: response.status,
        statusText: response.statusText,
        body: errorText
      })
      return NextResponse.json(
        { error: '등록 중 오류가 발생했습니다.' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json({ success: true, id: data.id })
  } catch (error) {
    console.error('Premium signup error:', error)
    return NextResponse.json(
      { error: '서버 오류가 발생했습니다.' },
      { status: 500 }
    )
  }
}
