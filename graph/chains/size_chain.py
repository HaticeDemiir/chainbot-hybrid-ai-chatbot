from langchain_core.runnables import RunnableLambda
from langchain_community.graphs import Neo4jGraph
import os

graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
    database=os.getenv("NEO4J_DATABASE")
)

def size_chain():
    def inner(state):
        if not state or not isinstance(state, dict):
            return {"generation": "Sistem verisi alınamadı. Lütfen tekrar deneyin."}

        uid = state.get("uid")
        if not uid:
            return {"generation": "Lütfen önce kullanıcı ID’nizi girin."}

        try:

            beden_tipi = input("Hangi beden bilgisini öğrenmek istiyorsunuz? (Giyim/Ayakkabı): ").strip().lower()

            if beden_tipi not in ["giyim", "ayakkabı", "ayakkabi"]:
                return {"generation": "Geçerli bir seçenek belirtin: Giyim veya Ayakkabı."}


            giyim_kod_map = {
                "XS": "6779", "S": "6785", "M": "6738", "L": "6797",
                "XL": "6795", "2XL": "6758"
            }

            ayakkabi_kod_map = {
                "Kadın": {
                    36: "7964", 37: "8063", 38: "7967", 39: "8064",
                    40: "7968", 41: "8251"
                },
                "Erkek": {
                    40: "7968", 41: "8251", 42: "9352", 43: "8069",
                    44: "9351", 45: "8068"
                }
            }

            if beden_tipi == "giyim":

                result = graph.query("""
                                   MATCH (u:UID {value: $uid})-[:HAS_SIZE]->(s:Size)
                                   RETURN s.beden AS beden, s.gender AS gender
                               """, params={"uid": uid})
                if result and result[0].get("beden"):
                    beden = result[0]['beden']
                    gender = result[0].get("gender")
                    link = f"https://www.lcwaikiki.de/tr-TR/DE/{'kadin' if gender == 'Kadın' else 'erkek'}/giyim?LastFilter=sizeheight&sizeheight={giyim_kod_map.get(beden)}"
                    return {"generation": f"Sistemde kayıtlı giyim bedeniniz: {beden}\n[LC Waikiki’de bu bedendeki {gender.lower()} giyim ürünlerine göz atın]({link})"}


                gender = graph.query("""
                                                            MATCH (u:UID {value:$uid})-[r:HAS_NAME]->(n)
                                                            WHERE n.gender IS NOT NULL
                                                            RETURN n.gender AS gender
                                                        """, params={"uid": uid})

                if gender and gender[0].get("gender"):
                    gender = gender[0]["gender"].strip().capitalize()
                else:
                    gender = input("Cinsiyetiniz nedir? (Kadın/Erkek): ").strip().capitalize()
                    graph.query("""
                                                                                    MATCH (u:UID {value: $uid})
                                                                                    MATCH (n:Name)
                                                                                    MERGE (u)-[:HAS_NAME]->(n)
                                                                                    SET n.gender = $gender
                                                                                """,
                                params={"uid": uid, "gender": gender})
                if gender not in ["Kadın", "Erkek", "Bebek"]:
                    return {"generation": "Geçerli bir cinsiyet belirtin: Kadın, Erkek veya Bebek."}

                try:
                    if gender == "Bebek":
                        boy = int(input("Bebek boyu (cm): "))
                    gogus = int(input("Göğüs ölçüsü (cm): "))
                    bel = int(input("Bel ölçüsü (cm): "))
                    basen = int(input("Basen ölçüsü (cm): "))
                    ic_bacak = int(input("İç bacak boyu (cm): "))
                except ValueError:
                    return {"generation": "Lütfen ölçüleri sayısal olarak girin."}

                query = """
                           MATCH (s:Size {gender: $gender})-[:HAS_MEASUREMENT]->(m:Measurement)
                           RETURN s.beden AS beden, m.gogus AS gogus, m.bel AS bel, m.basen AS basen, m.ic_bacak AS ic_bacak, m.boy AS boy
                       """
                sizes = graph.query(query, params={"gender": gender})
                if not sizes:
                    return {"generation": f"{gender} için beden bilgisi bulunamadı."}

                def hesapla_fark(s):
                    toplam_fark = 0
                    if gender == "Bebek":
                        toplam_fark += abs((s.get("boy") or 0) - boy)
                    toplam_fark += abs((s.get("gogus") or 0) - gogus)
                    toplam_fark += abs((s.get("bel") or 0) - bel)
                    toplam_fark += abs((s.get("basen") or 0) - basen)
                    toplam_fark += abs((s.get("ic_bacak") or 0) - ic_bacak)
                    return toplam_fark

                en_uygun = min(sizes, key=hesapla_fark)
                tahmini_beden = en_uygun["beden"]

                graph.query("""
                           MATCH (u:UID {value: $uid})
                           MATCH (s:Size {beden: $beden, gender: $gender})
                           MERGE (u)-[:HAS_SIZE]->(s)
                       """, params={"uid": uid, "beden": tahmini_beden, "gender": gender})

                kod = giyim_kod_map.get(tahmini_beden)
                link = f"https://www.lcwaikiki.de/tr-TR/DE/{'kadin' if gender == 'Kadın' else 'erkek'}/giyim?LastFilter=sizeheight&sizeheight={kod}"
                return {
                    "generation": f"Ölçülerinize göre tahmini giyim bedeniniz: {tahmini_beden}\n[LC Waikiki’de bu bedendeki {gender.lower()} giyim ürünlerine göz atın]({link})"}

            else:
                gender_result = graph.query("""
                                            MATCH (u:UID {value:$uid})-[r:HAS_NAME]->(n)
                                            WHERE n.gender IS NOT NULL
                                            RETURN n.gender AS gender
                                        """, params={"uid": uid})

                if gender_result and gender_result[0].get("gender"):
                    gender = gender_result[0]["gender"].capitalize()
                else:
                    gender = input("Cinsiyetiniz nedir? (Kadın/Erkek): ").strip().capitalize()
                    graph.query("""
                                                                    MATCH (u:UID {value: $uid})
                                                                    MATCH (n:Name)
                                                                    MERGE (u)-[:HAS_NAME]->(n)
                                                                    SET n.gender = $gender
                                                                """, params={"uid": uid, "gender": gender})

                result = graph.query("""
                                   MATCH (u:UID {value: $uid})-[:HAS_SHOE_SIZE]->(s:ShoeSize)
                                   RETURN s.numara AS numara
                               """, params={"uid": uid})
                if result and result[0].get("numara"):
                    kod = ayakkabi_kod_map[gender].get(result[0].get("numara"))
                    link = f"https://www.lcwaikiki.de/tr-TR/DE/{'kadin' if gender == 'Kadın' else 'erkek'}/ayakkabi?size={kod})"
                    return {
                        "generation": f"Sistemde kayıtlı ayakkabı numaranız: {result[0].get('numara')}\n[LC Waikiki’de bu numaradaki ayakkabılara göz atın]({link})"}

                try:
                    cm = int(input("Ayakk uzunluğunuzu girin (örnek: 25): "))
                except ValueError:
                    return {"generation": "Lütfen geçerli ölçüm girin."}
                mm = cm * 10

                ayakkabi = graph.query("""
                                   MATCH (s:ShoeSize {mm: $numara})
                                   RETURN s.numara AS Numara
                               """, params={"numara": mm})

                if not ayakkabi:
                    return {"generation": "Bu numarada bir ayakkabı bulunamadı."}


                graph.query("""
                                   MATCH (u:UID {value: $uid})
                                   MATCH (s:ShoeSize {mm: $mm})
                                   MERGE (u)-[:HAS_SHOE_SIZE]->(s)
                                   RETURN s.numara AS numara
                               """, params={"uid": uid, "mm": mm})

                return {"generation": f"Ayakkabı numaranız {ayakkabi} olarak kaydedildi."}

        except Exception as e:
            return {"generation": f"Bir hata oluştu: {str(e)}"}

    return RunnableLambda(inner)