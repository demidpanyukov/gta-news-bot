import asyncio
import feedparser
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# --- НАСТРОЙКИ ---
BOT_TOKEN = '8667142122:AAFYJe4FP0W7NIXXTOQXDFWxkYkSCvRR8WY' 

# ВАШ CHAT ID (замените на ваш реальный ID, который бот выдал при команде /start)
MY_CHAT_ID = 123456789  

KEYWORDS = ['gta 6', 'gta vi', 'grand theft auto', 'rockstar', 'gta']

RSS_FEEDS = [
    "https://www.rockstargames.com/newswire/feed", 
    "https://www.youtube.com/feeds/videos.xml?channel_id=UC6VcWc1rAoWdBCM0JxrRQ3A", 
    "https://feeds.ign.com/ign/games-all", 
    "https://www.gamespot.com/feeds/news/", 
    "https://www.pcgamer.com/rss/", 
    "https://www.eurogamer.net/feed", 
    "https://www.vg247.com/feed", 
    "https://www.polygon.com/rss/index.xml", 
    "https://www.rockpapershotgun.com/feed", 
    "https://www.gamesradar.com/feeds.xml", 
    "https://screenrant.com/feed/", 
    "https://gamerant.com/feed/", 
    "https://www.dualshockers.com/feed/", 
    "https://www.pushsquare.com/feeds/latest", 
    "https://www.purexbox.com/feeds/latest", 
]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
seen_links = set()

# Настройки часового пояса
MOSCOW_TZ = ZoneInfo('Europe/Moscow')

def get_all_news():
    """Собирает новости и возвращает список"""
    all_found = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if entry.link in seen_links:
                    continue
                
                text_to_check = (entry.title + " " + getattr(entry, 'summary', '')).lower()
                if any(keyword in text_to_check for keyword in KEYWORDS):
                    published_time = getattr(entry, 'published_parsed', None)
                    if published_time:
                        dt = datetime.fromtimestamp(datetime(*published_time[:6]).timestamp())
                    else:
                        dt = datetime.min 
                        
                    all_found.append({
                        'title': entry.title,
                        'link': entry.link,
                        'date': dt
                    })
        except Exception as e:
            print(f"Ошибка с лентой {url}: {e}")
    
    all_found.sort(key=lambda x: x['date'], reverse=True)
    return all_found[:10]

async def send_daily_digest(target_chat_id):
    """Отправляет дайджест"""
    if not target_chat_id or target_chat_id == 123456789:
        print("ВНИМАНИЕ: Укажите ваш реальный Chat ID в переменной MY_CHAT_ID, иначе бот не знает, куда слать новости.")
        return

    print("Собираю новости для дайджеста...")
    top_news = await asyncio.to_thread(get_all_news)
    
    if not top_news:
        await bot.send_message(chat_id=target_chat_id, text="📭 За это время новых новостей про GTA VI не найдено.")
        return

    message_text = "📰 **Дайджест новостей про GTA VI**\n\n"
    for i, news in enumerate(top_news, 1):
        message_text += f"{i}. [{news['title']}]({news['link']})\n\n"
        seen_links.add(news['link'])
        
    await bot.send_message(chat_id=target_chat_id, text=message_text, parse_mode="Markdown", disable_web_page_preview=True)
    print("Дайджест отправлен!")

async def scheduler():
    """Планировщик задач (работает по московскому времени)"""
    while True:
        now = datetime.now(MOSCOW_TZ)
        
        morning = now.replace(hour=7, minute=30, second=0, microsecond=0)
        evening = now.replace(hour=21, minute=0, second=0, microsecond=0)
        
        if now < morning:
            next_run = morning
        elif now < evening:
            next_run = evening
        else:
            next_run = morning + timedelta(days=1)
            
        wait_seconds = (next_run - now).total_seconds()
        print(f"Следующая проверка новостей: {next_run.strftime('%d.%m.%Y %H:%M')} (МСК). Жду...")
        
        await asyncio.sleep(wait_seconds)
        
        # Планировщик отправляет новости на ваш жестко заданный ID
        await send_daily_digest(MY_CHAT_ID)

# --- ОБРАБОТЧИКИ КОМАНД ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"Привет! Я бот для новостей GTA VI.\nЯ буду присылать дайджест **дважды в день (в 7:30 и 21:00 по МСК)**.\nА по команде `/news` я могу прислать новости прямо сейчас!")
    print(f"Кто-то нажал /start. Chat ID: {message.chat.id}. Если это вы и ID отличается от MY_CHAT_ID, обновите его в коде.")

@dp.message(Command("news"))
async def cmd_news(message: types.Message):
    await message.answer("🔄 Запускаю внеплановый сбор новостей. Это может занять до 15 секунд...")
    await send_daily_digest(MY_CHAT_ID)

# -------------------------

async def main():
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())