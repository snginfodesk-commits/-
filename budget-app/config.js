// הגדרות החיבור ל-Supabase. שני הערכים האלה ציבוריים מטבעם (ה-anon key נועד לדפדפן),
// וההגנה על הנתונים נעשית בכללי ה-Row Level Security שבקובץ supabase/schema.sql.
// כל עוד הערכים ריקים, האתר רץ ב"מצב הדגמה" ושומר נתונים רק בדפדפן.
window.BUDGET_CONFIG = {
  supabaseUrl: "",      // לדוגמה: https://abcdefghijkl.supabase.co
  supabaseAnonKey: "",  // Project Settings -> API -> anon public
  googleLogin: false    // true רק אחרי שהפעלתם את ספק Google ב-Supabase
};
