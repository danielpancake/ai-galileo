using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using MongoDB.Driver;
using MongoDB.Bson;
using UnityEngine.Networking;
using System;
using TMPro;
using UnityEngine.UI;
using System.IO;
using System.Net;
using Random = System.Random;

public class Model_Story
{
    public ObjectId _id { set; get; }
    public ObjectId suggested_topic_id { set; get; }
    public string theme { set; get; }
    public List<Model_StoryNode> story_intro { set; get; }
    public List<Model_StoryNode> story { set; get; }
    public List<Model_StoryNode> story_outro { set; get; }
    public string requested_by { set; get; }
}

public enum StoryPart
{
    Pre,
    Story,
    Post
}

public class Model_StoryNode
{
    public string type { set; get; }
    public string voice { set; get; }
    public string action { set; get; }
    public string image { set; get; }
    public string text { set; get; }
}

public class MongoViewer : MonoBehaviour
{
    private const string MONGO_URI = "mongodb://localhost:27017";
    private const string MONGO_DATABASE = "ai_galileo";
    private MongoClient client;
    private IMongoDatabase db;

    private List<Model_Story> stories;

    private AudioSource audioSource;

    public GameObject pushnoy;
    public AudioClip sitcomLaughTrack;
    public Image image;

    private int current_story = 0;
    private StoryPart current_story_part = StoryPart.Pre;
    private int current_node = 0;

    [SerializeField]
    public GameObject textMeshContainer;

    private TextMeshProUGUI textMesh;

    void Start()
    {
        client = new MongoClient(MONGO_URI);
        db = client.GetDatabase(MONGO_DATABASE);

        stories = getStories();

        textMesh = textMeshContainer.GetComponent<TextMeshProUGUI>();

        PlayNextClip();
    }

    private void Awake()
    {
        audioSource = gameObject.AddComponent<AudioSource>();
    }

    List<Model_Story> getStories()
    {
        // Retrieve all stories
        return db.GetCollection<Model_Story>("stories").Find(_ => true).ToList();
    }

    Model_StoryNode getCurrentNode(Model_Story story)
    {
        switch (current_story_part)
        {
            default:
            case StoryPart.Pre:
                return story.story_intro[current_node];
            case StoryPart.Story:
                return story.story[current_node];
            case StoryPart.Post:
                return story.story_outro[current_node];
        }
    }

    void PlayNextClip()
    {
        Model_Story story = stories[current_story];
        Model_StoryNode node = getCurrentNode(story);

        bool next_text_found = false;
        while (!next_text_found)
        {
            switch (node.type)
            {
                case "text":
                    next_text_found = true;
                    break;

                case "image":
                    StartCoroutine(FindLoadAndShow(node.image));

                    IncementNode();
                    node = getCurrentNode(story);
                    break;

                case "action":
                    if (node.action.Contains("прыг"))
                    {
                        pushnoy.GetComponent<Character>().Jump();
                    }
                    else if (node.action.Contains("смех"))
                    {
                        audioSource.PlayOneShot(sitcomLaughTrack);
                    }

                    IncementNode();
                    node = getCurrentNode(story);
                    break;

                default:
                    IncementNode();
                    node = getCurrentNode(story);

                    // TODO: prevent infinite loop
                    break;
            }
        }

        switch (node.type)
        {
            case "text":
                Debug.Log(node.text);
                textMesh.text = node.text;
                if (node.voice != null)
                {
                    StartCoroutine(LoadAndPlay(node.voice));
                }
                break;
        }
    }

    private void IncementNode()
    {
        current_node += 1;

        // Check if we are at the end of the current story part
        List<Model_StoryNode> current_story_part_list;

        switch (current_story_part)
        {
            default:
            case StoryPart.Pre:
                current_story_part_list = stories[current_story].story_intro;
                break;
            case StoryPart.Story:
                current_story_part_list = stories[current_story].story;
                break;
            case StoryPart.Post:
                current_story_part_list = stories[current_story].story_outro;
                break;
        }


        if (current_node >= current_story_part_list.Count)
        {
            if (current_story_part == StoryPart.Pre)
            {
                current_story_part = StoryPart.Story;
                current_node = 0;
            }
            else if (current_story_part == StoryPart.Story)
            {
                current_story_part = StoryPart.Post;
                current_node = 0;
            }
            else if (current_story_part == StoryPart.Post)
            {
                current_story += 1;
                current_story_part = StoryPart.Pre;
                current_node = 0;
            }
        }

        // Check if we are at the end of the stories
        if (current_story >= stories.Count)
        {
            current_story = 0;
            current_node = 0;
        }
    }
    private string GetHtmlCode(string query)
    {
        string url = "https://www.google.com/search?q=" + query + "&tbm=isch";
        string data = "";

        var request = (HttpWebRequest)WebRequest.Create(url);
        var response = (HttpWebResponse)request.GetResponse();

        using (Stream dataStream = response.GetResponseStream())
        {
            if (dataStream == null)
                return "";
            using (var sr = new StreamReader(dataStream))
            {
                data = sr.ReadToEnd();
            }
        }
        return data;
    }

    private List<string> GetUrls(string html)
    {
        var urls = new List<string>();
        int ndx = html.IndexOf("<img", StringComparison.Ordinal);
        int max_tries = 20000;

        while (ndx >= 0 && max_tries >= 0)
        {
            ndx = html.IndexOf("src=\"", ndx, StringComparison.Ordinal);
            ndx = ndx + 5;
            int ndx2 = html.IndexOf("\"", ndx, StringComparison.Ordinal);
            string url = html.Substring(ndx, ndx2 - ndx);
            urls.Add(url);
            ndx = html.IndexOf("<img", ndx, StringComparison.Ordinal);
            max_tries--;
        }
        return urls;
    }

    IEnumerator FindLoadAndShow(string query)
    {
        string html = GetHtmlCode(query);
        List<string> urls = GetUrls(html);

        Random rnd = new System.Random();
        int randomUrl = rnd.Next(0, urls.Count - 1);

        UnityWebRequest www = UnityWebRequest.Get(urls[randomUrl]);
        yield return www.SendWebRequest();

        if (www.isNetworkError || www.isHttpError)
        {
            Debug.Log(www.error);
        }
        else
        {
            Texture2D texture = new Texture2D(2, 2);
            texture.LoadImage(www.downloadHandler.data);
            Sprite sprite = Sprite.Create(texture, new Rect(0, 0, texture.width, texture.height), new Vector2(0.5f, 0.5f));

            image.sprite = sprite;
        }
    }

    IEnumerator LoadAndPlay(string filepath)
    {
        WWW www = new("file://" + filepath);
        yield return www;

        while (!www.isDone)
        {
            yield return null;
        }

        audioSource.clip = www.GetAudioClip(false);
        audioSource.Play();

        while (audioSource.isPlaying)
        {
            yield return null;
        }

        IncementNode();
        PlayNextClip();
    }
}
