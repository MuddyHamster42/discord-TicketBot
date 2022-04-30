import os


def load_cogs(bot):

    utils_folder = os.path.dirname(__file__)
    main_folder = os.path.dirname(utils_folder)
    cogs_folder = os.path.join(main_folder, "cogs")

    print("\n======= Loading cogs =======")
    for filename in os.listdir(cogs_folder):
        if filename.endswith(".py"):
            bot.load_extension(f"cogs.{filename[:-3]}")
            print(f">> {filename}")
    print("======= Cogs loaded! =======\n")