// הגדרות החיבור ל-Supabase. שני הערכים האלה ציבוריים מטבעם (ה-anon key נועד לדפדפן),
// וההגנה על הנתונים נעשית בכללי ה-Row Level Security שבקובץ supabase/schema.sql.
// אם הערכים ריקים, האתר רץ ב"מצב הדגמה" ושומר נתונים רק בדפדפן.
window.BUDGET_CONFIG = {
  supabaseUrl: "https://srzjatdvsvvchirmhvuy.supabase.co",
  supabaseAnonKey: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNyemphdGR2c3Z2Y2hpcm1odnV5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQ5OTY0NDEsImV4cCI6MjExMDU3MjQ0MX0.8jDXVOQCpngPI7ezYiI5pWm_64z7ntC8PofC5Wftcb4", // Project Settings -> API -> anon public
  googleLogin: false    // true רק אחרי שהפעלתם את ספק Google ב-Supabase
};
