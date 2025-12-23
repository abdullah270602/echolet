import { neon } from "@neondatabase/serverless";

// Artificial base count to show social proof
const BASE_COUNT = 37;

// Validation constants
const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
const NAME_REGEX = /^[a-zA-Z\s\-'.]+$/;
const MAX_NAME_LENGTH = 100;
const MAX_EMAIL_LENGTH = 254;

// Sanitize string - remove any potentially dangerous characters
function sanitize(str: string): string {
  return str
    .trim()
    .replace(/[<>]/g, "") // Remove HTML brackets
    .slice(0, 255); // Limit length
}

export default async function handler(
  req: { method?: string; body?: { name?: string; email?: string } },
  res: { status: (code: number) => { json: (data: unknown) => void } }
) {
  const sql = neon(process.env.DATABASE_URL!);

  // GET - Return waitlist count
  if (req.method === "GET") {
    try {
      const result = await sql`SELECT COUNT(*) as count FROM waitlist`;
      const dbCount = parseInt(result[0].count as string, 10) || 0;
      return res.status(200).json({ count: BASE_COUNT + dbCount });
    } catch (error) {
      console.error("Waitlist count error:", error);
      return res.status(200).json({ count: BASE_COUNT });
    }
  }

  // POST - Add to waitlist
  if (req.method === "POST") {
    try {
      const { name: rawName, email: rawEmail } = req.body || {};

      // Validate name
      if (!rawName || typeof rawName !== "string") {
        return res.status(400).json({ error: "Name is required" });
      }

      const name = sanitize(rawName);

      if (name.length < 2) {
        return res.status(400).json({ error: "Name must be at least 2 characters" });
      }

      if (name.length > MAX_NAME_LENGTH) {
        return res.status(400).json({ error: "Name is too long" });
      }

      if (!NAME_REGEX.test(name)) {
        return res.status(400).json({ error: "Name contains invalid characters" });
      }

      // Validate email
      if (!rawEmail || typeof rawEmail !== "string") {
        return res.status(400).json({ error: "Email is required" });
      }

      const email = sanitize(rawEmail).toLowerCase();

      if (email.length > MAX_EMAIL_LENGTH) {
        return res.status(400).json({ error: "Email is too long" });
      }

      if (!EMAIL_REGEX.test(email)) {
        return res.status(400).json({ error: "Please enter a valid email address" });
      }

      // Insert into waitlist (ignore if email already exists)
      // Note: Neon's tagged template literals automatically escape values (SQL injection safe)
      await sql`
        INSERT INTO waitlist (name, email, created_at)
        VALUES (${name}, ${email}, NOW())
        ON CONFLICT (email) DO NOTHING
      `;

      // Return updated count
      const result = await sql`SELECT COUNT(*) as count FROM waitlist`;
      const dbCount = parseInt(result[0].count as string, 10) || 0;

      return res
        .status(200)
        .json({ success: true, count: BASE_COUNT + dbCount });
    } catch (error) {
      console.error("Waitlist error:", error);
      return res.status(500).json({ error: "Failed to join waitlist" });
    }
  }

  return res.status(405).json({ error: "Method not allowed" });
}
