import datetime
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from .models import Question, Choice


class QuestionModelTests(TestCase):
    """Test cases for the Question model."""

    def test_was_published_recently_with_future_question(self):
        """Test that was_published_recently returns False for questions with future pub_date."""  # noqa: E501
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """Test that was_published_recently returns False for questions older than 1 day."""  # noqa: E501
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=time)
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """Test that was_published_recently returns True for questions within the last day."""  # noqa: E501
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)

    def test_question_str_representation(self):
        """Test the string representation of Question model."""
        question = Question(question_text="Test question")
        self.assertEqual(str(question), "Test question")

    def test_choice_str_representation(self):
        """Test the string representation of Choice model."""
        question = Question.objects.create(
            question_text="Test question", pub_date=timezone.now()
        )
        choice = Choice(question=question, choice_text="Test choice")
        self.assertEqual(str(choice), "Test choice")


class QuestionIndexViewTests(TestCase):
    """Test cases for the index view."""

    def test_no_questions(self):
        """Test that the index view displays appropriate message when no questions exist."""  # noqa: E501
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])

    def test_past_question(self):
        """Test that past questions are displayed on the index page."""
        question = Question.objects.create(
            question_text="Past question.",
            pub_date=timezone.now() - datetime.timedelta(days=30),
        )
        response = self.client.get(reverse("index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [question],
        )

    def test_future_question(self):
        """Test that future questions are not displayed on the index page."""
        Question.objects.create(
            question_text="Future question.",
            pub_date=timezone.now() + datetime.timedelta(days=30),
        )
        response = self.client.get(reverse("index"))
        self.assertContains(response, "No polls are available.")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])

    def test_future_question_and_past_question(self):
        """Test that only past questions are displayed when both past and future exist."""  # noqa: E501
        past_question = Question.objects.create(
            question_text="Past question.",
            pub_date=timezone.now() - datetime.timedelta(days=30),
        )
        Question.objects.create(
            question_text="Future question.",
            pub_date=timezone.now() + datetime.timedelta(days=30),
        )
        response = self.client.get(reverse("index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [past_question],
        )

    def test_two_past_questions(self):
        """Test that multiple past questions are displayed in correct order."""
        question1 = Question.objects.create(
            question_text="Past question 1.",
            pub_date=timezone.now() - datetime.timedelta(days=30),
        )
        question2 = Question.objects.create(
            question_text="Past question 2.",
            pub_date=timezone.now() - datetime.timedelta(days=5),
        )
        response = self.client.get(reverse("index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [question2, question1],
        )


class QuestionDetailViewTests(TestCase):
    """Test cases for the detail view."""

    def test_future_question(self):
        """Test that detail view returns 404 for future questions."""
        future_question = Question.objects.create(
            question_text="Future question.",
            pub_date=timezone.now() + datetime.timedelta(days=5),
        )
        url = reverse("detail", args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """Test that detail view displays past questions."""
        past_question = Question.objects.create(
            question_text="Past Question.",
            pub_date=timezone.now() - datetime.timedelta(days=5),
        )
        url = reverse("detail", args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)


class QuestionResultsViewTests(TestCase):
    """Test cases for the results view."""

    def test_future_question_results(self):
        """Test that results view returns 404 for future questions."""
        future_question = Question.objects.create(
            question_text="Future question.",
            pub_date=timezone.now() + datetime.timedelta(days=5),
        )
        url = reverse("results", args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question_results(self):
        """Test that results view displays past questions."""
        past_question = Question.objects.create(
            question_text="Past Question.",
            pub_date=timezone.now() - datetime.timedelta(days=5),
        )
        url = reverse("results", args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)


class QuestionVoteViewTests(TestCase):
    """Test cases for the vote view."""

    def test_vote_with_valid_choice(self):
        """Test voting with a valid choice."""
        question = Question.objects.create(
            question_text="Test question.", pub_date=timezone.now()
        )
        choice = Choice.objects.create(
            question=question, choice_text="Test choice", votes=0
        )
        url = reverse("vote", args=(question.id,))
        response = self.client.post(url, {"choice": choice.id})
        self.assertRedirects(response, reverse("results", args=(question.id,)))

        # Check that the vote was recorded
        choice.refresh_from_db()
        self.assertEqual(choice.votes, 1)

    def test_vote_without_choice(self):
        """Test voting without selecting a choice."""
        question = Question.objects.create(
            question_text="Test question.", pub_date=timezone.now()
        )
        Choice.objects.create(question=question, choice_text="Test choice", votes=0)
        url = reverse("vote", args=(question.id,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You didn&#x27;t select a choice.")

    def test_vote_with_invalid_choice(self):
        """Test voting with an invalid choice ID."""
        question = Question.objects.create(
            question_text="Test question.", pub_date=timezone.now()
        )
        url = reverse("vote", args=(question.id,))
        response = self.client.post(url, {"choice": 999})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You didn&#x27;t select a choice.")

    def test_vote_on_future_question(self):
        """Test that voting on future questions returns 404."""
        future_question = Question.objects.create(
            question_text="Future question.",
            pub_date=timezone.now() + datetime.timedelta(days=5),
        )
        url = reverse("vote", args=(future_question.id,))
        response = self.client.post(url, {"choice": 1})
        self.assertEqual(response.status_code, 404)
