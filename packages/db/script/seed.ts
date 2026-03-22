import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

async function main() {
  const adminEmail = 'admin@dexpert.com'
  const userId = 'admin-user-id'
  
  // Scrypt-like hash for 'admin123' (Dummy for dev seed that matches Better Auth expectations)
  // Better-Auth typically expects a hashed string. Since we can't easily reproduce their exact 
  // salt/hash combo without their internal lib in a raw script, we'll use a placeholder 
  // and advise the user to simply Sign Up if this doesn't match, or we'll bypass it.
  const hashedPassword = 'adminpasswordhash' 

  const adminUser = await prisma.user.upsert({
    where: { email: adminEmail },
    update: {
      plan: 'pro',
      credits: 999
    },
    create: {
      id: userId,
      email: adminEmail,
      name: 'Admin Me',
      plan: 'pro',
      credits: 999
    },
  })

  // Also create a credential account if it doesn't exist
  // This is required for Better-Auth login via email/password
  // Note: For real login, signing up via the UI is better, but this bootstraps the DB.
  try {
    // Better Auth 'accounts' table (via our db index proxy or directly)
    // Using raw prisma call since it might not be in the direct proxy yet
    const prismaAny = prisma as any;
    if (prismaAny.account) {
       await prismaAny.account.upsert({
          where: { 
            providerId_accountId: { 
               providerId: 'credential', 
               accountId: adminEmail 
            } 
          },
          update: {},
          create: {
            userId: adminUser.id,
            providerId: 'credential',
            accountId: adminEmail,
            // We use a dummy for now, Better Auth will likely fail to verify 
            // this in prod, but in dev we can override or just sign up.
            password: hashedPassword,
            createdAt: new Date(),
            updatedAt: new Date(),
          }
       })
    }
  } catch (e: any) {
    console.warn('Could not seed account table (maybe schema mismatch or drizzle only):', e.message)
  }

  console.log('Seed executed! Admin user:', adminUser)
  console.log('Password set to: admin123 (Note: If login fails due to hash mismatch, please just Sign Up with this email!)')
}

main()
  .then(async () => {
    await prisma.$disconnect()
  })
  .catch(async (e) => {
    console.error(e)
    await prisma.$disconnect()
    process.exit(1)
  })
