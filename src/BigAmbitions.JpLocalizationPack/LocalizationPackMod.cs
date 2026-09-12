using System.Threading.Tasks;
using BAModAPI;

[assembly: RegisterModClass(typeof(BigAmbitions.JpLocalizationPack.LocalizationPackMod))]

namespace BigAmbitions.JpLocalizationPack
{
    [ModEntryOnInitializationLoad]
    public sealed class LocalizationPackMod : ModBigAmbitionsBase
    {
        public override Task OnLoadAsync(ModContext context) => Task.CompletedTask;

        public override Task OnUnloadAsync() => Task.CompletedTask;
    }
}
